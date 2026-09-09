drop table if exists features_property_type_classification;
create index idx_entity_property_stats_entity_id on entity_property_stats(entity_id);
analyze entity_property_stats;
create table features_property_type_classification as
select
    property_id,
    property_label,
    property_type,
    count(*) as num_entity_property_pairs,
    avg(epaav_num_distinct_values) as avg_epv_num_distinct_values,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_num_distinct_values) as median_epv_num_distinct_values,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_num_distinct_values)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_num_distinct_values) as iqr_epv_num_distinct_values,
    avg(epaav_num_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as avg_epv_num_changes_per_day,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_num_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as median_epv_num_changes_per_day,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_num_changes::float / GREATEST(es.entity_age_in_days, 1.0))
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_num_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as iqr_epv_num_changes_per_day,
    avg(epaav_num_changes_after_birth::float / GREATEST(es.entity_age_in_days, 1.0)) as avg_epv_num_changes_after_birth_per_day,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_num_changes_after_birth::float / GREATEST(es.entity_age_in_days, 1.0)) as median_epv_num_changes_after_birth_per_day,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_num_changes_after_birth::float / GREATEST(es.entity_age_in_days, 1.0))
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_num_changes_after_birth::float / GREATEST(es.entity_age_in_days, 1.0)) as iqr_epv_num_changes_after_birth_per_day,
    avg(epaav_avg_num_changes_per_value) as avg_epv_avg_num_changes_per_value,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_avg_num_changes_per_value) as median_epv_avg_num_changes_per_value,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_avg_num_changes_per_value)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_avg_num_changes_per_value) as iqr_epv_avg_num_changes_per_value,
    avg(epaav_pct_values_ever_changed) as avg_epv_pct_values_ever_changed,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_pct_values_ever_changed) as median_epv_pct_values_ever_changed,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_pct_values_ever_changed)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_pct_values_ever_changed) as iqr_epv_pct_values_ever_changed,
    avg(epaav_avg_time_between_updates_sec) as avg_epv_avg_time_between_updates_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_avg_time_between_updates_sec) as median_epv_avg_time_between_updates_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_avg_time_between_updates_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_avg_time_between_updates_sec) as iqr_epv_avg_time_between_updates_sec,
    count(*) FILTER (WHERE epaav_avg_time_between_updates_sec IS NULL)::float / count(*) as null_rate_epv_avg_time_between_updates_sec,
    avg(epaav_avg_median_time_between_updates_sec) as avg_epv_avg_median_time_between_updates_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_avg_median_time_between_updates_sec) as median_epv_avg_median_time_between_updates_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_avg_median_time_between_updates_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_avg_median_time_between_updates_sec) as iqr_epv_avg_median_time_between_updates_sec,
    count(*) FILTER (WHERE epaav_avg_median_time_between_updates_sec IS NULL)::float / count(*) as null_rate_epv_avg_median_time_between_updates_sec,
    avg(epaav_min_time_between_updates_sec) as avg_epv_min_time_between_updates_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_min_time_between_updates_sec) as median_epv_min_time_between_updates_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_min_time_between_updates_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_min_time_between_updates_sec) as iqr_epv_min_time_between_updates_sec,
    count(*) FILTER (WHERE epaav_min_time_between_updates_sec IS NULL)::float / count(*) as null_rate_epv_min_time_between_updates_sec,
    avg(epaav_max_time_between_updates_sec) as avg_epv_max_time_between_updates_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_max_time_between_updates_sec) as median_epv_max_time_between_updates_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_max_time_between_updates_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_max_time_between_updates_sec) as iqr_epv_max_time_between_updates_sec,
    count(*) FILTER (WHERE epaav_max_time_between_updates_sec IS NULL)::float / count(*) as null_rate_epv_max_time_between_updates_sec,
    avg(epaav_avg_age_of_value_at_update_sec) as avg_epv_avg_age_of_value_at_update_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_avg_age_of_value_at_update_sec) as median_epv_avg_age_of_value_at_update_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_avg_age_of_value_at_update_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_avg_age_of_value_at_update_sec) as iqr_epv_avg_age_of_value_at_update_sec,
    count(*) FILTER (WHERE epaav_avg_age_of_value_at_update_sec IS NULL)::float / count(*) as null_rate_epv_avg_age_of_value_at_update_sec,
    avg(epaav_num_close_in_time_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as avg_epv_num_close_in_time_changes_per_day,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_num_close_in_time_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as median_epv_num_close_in_time_changes_per_day,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_num_close_in_time_changes::float / GREATEST(es.entity_age_in_days, 1.0))
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_num_close_in_time_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as iqr_epv_num_close_in_time_changes_per_day,
    avg(epaav_pct_all_changes_close_in_time) as avg_epv_pct_all_changes_close_in_time,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_pct_all_changes_close_in_time) as median_epv_pct_all_changes_close_in_time,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_pct_all_changes_close_in_time)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_pct_all_changes_close_in_time) as iqr_epv_pct_all_changes_close_in_time,
    avg(epaav_avg_time_between_changes_not_close_in_time_sec) as avg_epv_avg_time_bc_nc_in_time_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_avg_time_between_changes_not_close_in_time_sec) as median_epv_avg_time_bc_nc_in_time_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_avg_time_between_changes_not_close_in_time_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_avg_time_between_changes_not_close_in_time_sec) as iqr_epv_avg_time_bc_nc_in_time_sec,
    count(*) FILTER (WHERE epaav_avg_time_between_changes_not_close_in_time_sec IS NULL)::float / count(*) as null_rate_epv_avg_time_bc_nc_in_time_sec,
    avg(epaav_min_time_between_changes_not_close_in_time_sec) as avg_epv_min_time_bc_nc_in_time_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_min_time_between_changes_not_close_in_time_sec) as median_epv_min_time_bc_nc_in_time_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_min_time_between_changes_not_close_in_time_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_min_time_between_changes_not_close_in_time_sec) as iqr_epv_min_time_bc_nc_in_time_sec,
    count(*) FILTER (WHERE epaav_min_time_between_changes_not_close_in_time_sec IS NULL)::float / count(*) as null_rate_epv_min_time_bc_nc_in_time_sec,
    avg(epaav_max_time_between_changes_not_close_in_time_sec) as avg_epv_max_time_bc_nc_in_time_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epaav_max_time_between_changes_not_close_in_time_sec) as median_epv_max_time_bc_nc_in_time_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epaav_max_time_between_changes_not_close_in_time_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epaav_max_time_between_changes_not_close_in_time_sec) as iqr_epv_max_time_bc_nc_in_time_sec,
    avg(epoa_num_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as avg_ep_num_changes_per_day,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_num_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as median_ep_num_changes_per_day,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_num_changes::float / GREATEST(es.entity_age_in_days, 1.0))
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_num_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as iqr_ep_num_changes_per_day,
    avg(epoa_num_distinct_values) as avg_ep_num_distinct_values,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_num_distinct_values) as median_ep_num_distinct_values,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_num_distinct_values)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_num_distinct_values) as iqr_ep_num_distinct_values,
    avg(epoa_avg_time_between_changes_sec) as avg_ep_avg_time_bc_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_avg_time_between_changes_sec) as median_ep_avg_time_bc_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_avg_time_between_changes_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_avg_time_between_changes_sec) as iqr_ep_avg_time_bc_sec,
    count(*) FILTER (WHERE epoa_avg_time_between_changes_sec IS NULL)::float / count(*) as null_rate_ep_avg_time_bc_sec,
    avg(epoa_min_time_between_changes_sec) as avg_ep_min_time_bc_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_min_time_between_changes_sec) as median_ep_min_time_bc_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_min_time_between_changes_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_min_time_between_changes_sec) as iqr_ep_min_time_bc_sec,
    count(*) FILTER (WHERE epoa_min_time_between_changes_sec IS NULL)::float / count(*) as null_rate_ep_min_time_bc_sec,
    avg(epoa_max_time_between_changes_sec) as avg_ep_max_time_bc_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_max_time_between_changes_sec) as median_ep_max_time_bc_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_max_time_between_changes_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_max_time_between_changes_sec) as iqr_ep_max_time_bc_sec,
    count(*) FILTER (WHERE epoa_max_time_between_changes_sec IS NULL)::float / count(*) as null_rate_ep_max_time_bc_sec,
    avg(epoa_median_time_between_updates_sec) as avg_ep_median_time_between_updates_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_median_time_between_updates_sec) as median_ep_median_time_between_updates_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_median_time_between_updates_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_median_time_between_updates_sec) as iqr_ep_median_time_between_updates_sec,
    count(*) FILTER (WHERE epoa_median_time_between_updates_sec IS NULL)::float / count(*) as null_rate_ep_median_time_between_updates_sec,
    avg(epoa_num_close_in_time_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as avg_ep_num_close_in_time_changes_per_day,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_num_close_in_time_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as median_ep_num_close_in_time_changes_per_day,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_num_close_in_time_changes::float / GREATEST(es.entity_age_in_days, 1.0))
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_num_close_in_time_changes::float / GREATEST(es.entity_age_in_days, 1.0)) as iqr_ep_num_close_in_time_changes_per_day,
    avg(epoa_avg_time_between_changes_not_close_in_time_sec) as avg_ep_avg_time_bc_nc_in_time_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_avg_time_between_changes_not_close_in_time_sec) as median_ep_avg_time_bc_nc_in_time_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_avg_time_between_changes_not_close_in_time_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_avg_time_between_changes_not_close_in_time_sec) as iqr_ep_avg_time_bc_nc_in_time_sec,
    count(*) FILTER (WHERE epoa_avg_time_between_changes_not_close_in_time_sec IS NULL)::float / count(*) as null_rate_ep_avg_time_bc_nc_in_time_sec,
    avg(epoa_min_time_between_changes_not_close_in_time_sec) as avg_ep_min_time_bc_nc_in_time_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_min_time_between_changes_not_close_in_time_sec) as median_ep_min_time_bc_nc_in_time_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_min_time_between_changes_not_close_in_time_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_min_time_between_changes_not_close_in_time_sec) as iqr_ep_min_time_bc_nc_in_time_sec,
    count(*) FILTER (WHERE epoa_min_time_between_changes_not_close_in_time_sec IS NULL)::float / count(*) as null_rate_ep_min_time_bc_nc_in_time_sec,
    avg(epoa_max_time_between_changes_not_close_in_time_sec) as avg_ep_max_time_bc_nc_in_time_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_max_time_between_changes_not_close_in_time_sec) as median_ep_max_time_bc_nc_in_time_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_max_time_between_changes_not_close_in_time_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_max_time_between_changes_not_close_in_time_sec) as iqr_ep_max_time_bc_nc_in_time_sec,
    count(*) FILTER (WHERE epoa_max_time_between_changes_not_close_in_time_sec IS NULL)::float / count(*) as null_rate_ep_max_time_bc_nc_in_time_sec,
    avg(epoa_num_value_creates::float / GREATEST(es.entity_age_in_days, 1.0)) as avg_ep_num_value_creates_per_day,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_num_value_creates::float / GREATEST(es.entity_age_in_days, 1.0)) as median_ep_num_value_creates_per_day,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_num_value_creates::float / GREATEST(es.entity_age_in_days, 1.0))
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_num_value_creates::float / GREATEST(es.entity_age_in_days, 1.0)) as iqr_ep_num_value_creates_per_day,
    avg(epoa_num_real_updates::float / GREATEST(es.entity_age_in_days, 1.0)) as avg_ep_num_real_updates_per_day,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_num_real_updates::float / GREATEST(es.entity_age_in_days, 1.0)) as median_ep_num_real_updates_per_day,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_num_real_updates::float / GREATEST(es.entity_age_in_days, 1.0))
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_num_real_updates::float / GREATEST(es.entity_age_in_days, 1.0)) as iqr_ep_num_real_updates_per_day,
    avg(epoa_num_value_id_real_updated) as avg_ep_num_value_id_real_updated,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_num_value_id_real_updated) as median_ep_num_value_id_real_updated,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_num_value_id_real_updated)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_num_value_id_real_updated) as iqr_ep_num_value_id_real_updated,
    avg(epoa_avg_age_of_value_to_first_insert_sec) as avg_ep_avg_age_of_value_to_first_insert_sec,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_avg_age_of_value_to_first_insert_sec) as median_ep_avg_age_of_value_to_first_insert_sec,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_avg_age_of_value_to_first_insert_sec)
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_avg_age_of_value_to_first_insert_sec) as iqr_ep_avg_age_of_value_to_first_insert_sec,
    count(*) FILTER (WHERE epoa_avg_age_of_value_to_first_insert_sec IS NULL)::float / count(*) as null_rate_ep_avg_age_of_value_to_first_insert_sec,
    avg(epoa_num_close_in_time_changes::float / nullif(epoa_num_changes - 1, 0)) as avg_pct_gaps_are_close_in_time,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY epoa_num_close_in_time_changes::float / nullif(epoa_num_changes - 1, 0)) as median_pct_gaps_are_close_in_time,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY epoa_num_close_in_time_changes::float / nullif(epoa_num_changes - 1, 0))
    - percentile_cont(0.25) WITHIN GROUP (ORDER BY epoa_num_close_in_time_changes::float / nullif(epoa_num_changes - 1, 0)) as iqr_pct_gaps_are_close_in_time
from entity_property_stats eps
join entity_stats es on es.entity_id = eps.entity_id
group by property_id, property_label, property_type;