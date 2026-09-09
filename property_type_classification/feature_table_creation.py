# gen_property_features.py — emits the property-level aggregation over entity_property_stats
# Spec: (column, kind) where kind drives normalization + null handling:
#   'count'  -> normalized by GREATEST(entity_age_in_days, 1.0), aggregates avg/median/iqr
#   'ratio'  -> as-is, avg/median/iqr
#   'time'   -> as-is, avg/median/iqr + null_rate
#   'plain'  -> as-is, avg/median/iqr  (counts you deliberately don't normalize)

FEATURES = [
    # ---- epv ----
    ('epaav_num_distinct_values',                                   'plain'),
    ('epaav_num_changes',                                           'count'),
    ('epaav_num_changes_after_birth',                               'count'),
    ('epaav_avg_num_changes_per_value',                             'ratio'),
    ('epaav_pct_values_ever_changed',                               'ratio'),
    ('epaav_avg_time_between_updates_sec',                          'time'),
    ('epaav_avg_median_time_between_updates_sec',                   'time'),
    ('epaav_min_time_between_updates_sec',                           'time'),
    ('epaav_max_time_between_updates_sec',                           'time'),
    ('epaav_avg_age_of_value_at_update_sec',                        'time'),
    ('epaav_num_close_in_time_changes',                             'count'),
    ('epaav_pct_all_changes_close_in_time',                         'ratio'),
    ('epaav_avg_time_between_changes_not_close_in_time_sec',         'time'),
    ('epaav_min_time_between_changes_not_close_in_time_sec',         'time'),
    ('epaav_max_time_between_changes_not_close_in_time_sec','         time'),
    # ---- ep ----
    ('epoa_num_changes',                                            'count'),
    ('epoa_num_distinct_values',                                    'plain'),
    ('epoa_avg_time_between_changes_sec',                           'time'),
    ('epoa_min_time_between_changes_sec',                           'time'),
    ('epoa_max_time_between_changes_sec',                           'time'),
    ('epoa_median_time_between_updates_sec',                        'time'),
    ('epoa_num_close_in_time_changes',                              'count'),
    ('epoa_avg_time_between_changes_not_close_in_time_sec',         'time'),
    ('epoa_min_time_between_changes_not_close_in_time_sec',         'time'),
    ('epoa_max_time_between_changes_not_close_in_time_sec',         'time'),
    ('epoa_num_value_creates',                                      'count'),
    ('epoa_num_real_updates',                                       'count'),
    ('epoa_num_value_id_real_updated',                              'plain'),   # used in ratio below
    ('epoa_avg_age_of_value_to_first_insert_sec',                   'time'),
]

DERIVED = [
    # burst share at pair level: gaps = num_changes - 1
    ('pct_gaps_are_close_in_time',
     'epoa_num_close_in_time_changes::float / nullif(epoa_num_changes - 1, 0)')
]

NORM = 'GREATEST(es.entity_age_in_days, 1.0)'

def aggs(expr, name):
    return [
        f"    avg({expr}) as avg_{name.replace('epaav_', 'epv_').replace('epoa_', 'ep_').replace('between_changes', 'bc').replace('not_close', 'nc')}",
        f"    percentile_cont(0.5) WITHIN GROUP (ORDER BY {expr}) as median_{name.replace('epaav_', 'epv_').replace('epoa_', 'ep_').replace('between_changes', 'bc').replace('not_close', 'nc')}",
        f"    percentile_cont(0.75) WITHIN GROUP (ORDER BY {expr})\n"
        f"    - percentile_cont(0.25) WITHIN GROUP (ORDER BY {expr}) as iqr_{name.replace('epaav_', 'epv_').replace('epoa_', 'ep_').replace('between_changes', 'bc').replace('not_close', 'nc')}",
    ]

def emit():
    lines = [
        "drop table if exists features_property_type_classification;",
        "create index idx_entity_property_stats_entity_id on entity_property_stats(entity_id);",
        "analyze entity_property_stats;",
        "create table features_property_type_classification as",
        "select",
        "    property_id,",
        "    property_label,",
        "    property_type,",
        "    count(*) as num_entity_property_pairs,",
    ]
    body = []
    for col, kind in FEATURES:
        expr = f"{col}::float / {NORM}" if kind == 'count' else col
        name = f"{col}_per_day" if kind == 'count' else col
        body += aggs(expr, name)
        if kind == 'time':
            body.append(
                f"    count(*) FILTER (WHERE {col} IS NULL)::float / count(*)"
                f" as null_rate_{col.replace('epaav_', 'epv_').replace('epoa_', 'ep_').replace('between_changes', 'bc').replace('not_close', 'nc')}")
    for name, expr in DERIVED:
        body += aggs(expr, name)
    lines.append(",\n".join(body))
    lines += [
        "from entity_property_stats eps",
        "join entity_stats es on es.entity_id = eps.entity_id",
        "group by property_id, property_label, property_type;",
    ]
    return "\n".join(lines)


def generate_entity_property_stats_sql():


    init_query = """
        create index idx_entity_prop_overall_activity_entity_property on entity_prop_overall_activity(entity_id, property_id);
        analyze entity_prop_overall_activity;

        create index idx_entity_prop_avg_activity_of_values_entity_property on entity_prop_avg_activity_of_values(entity_id, property_id);
        analyze entity_prop_avg_activity_of_values;

        create table entity_property_stats as
        select 
            -- columns from entity_prop_distinct_val_change
            -- This table has information of all (entity, property) pairs that
            -- the other 2 may miss because they capture information about time between changes
            -- That's why the epdvc table is the anchor (left join) for the joins
            epdvc.property_id,
            p.property_label,
            epdvc.entity_id,
    """

    #TODO: ADD TO RUN THIS ON THE DB
    columns_names = """
        select string_agg(
            format('%s.%s as %s_%s', tbl.alias, c.column_name, tbl.alias, c.column_name),
            E',\n    ' order by tbl.ord, c.ordinal_position)
        from (values ('epdvc', 'entity_prop_distinct_val_change', 1),
                    ('epv', 'entity_prop_avg_activity_of_values', 2),
                    ('epoa',  'entity_prop_overall_activity', 3)) as tbl(alias, table_name, ord)
        join information_schema.columns c on c.table_name = tbl.table_name
        where c.column_name not in ('entity_id', 'property_id');
    """

    final_query = """
        p.property_type
        from 
            properties p 
            join entity_prop_distinct_val_change epdvc on p.property_id = epdvc.property_id
            left join entity_prop_avg_activity_of_values epaav on epaav.property_id = epdvc.property_id and epdvc.entity_id = epaav.entity_id
            left join entity_prop_overall_activity epoa on epoa.property_id = epdvc.property_id and epoa.entity_id = epdvc.entity_id;
    """

    full = init_query + columns_names + final_query

    with open("sql/entity_property_stats_test.sql", "w") as f:
        f.write(full)

if __name__ == "__main__":

    with open("sql/features_property_type_classification.sql", "w") as f:
        f.write(emit())
