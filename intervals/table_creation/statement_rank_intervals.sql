SET work_mem = '5GB';
create table statement_rank_intervals as
with rank_changes as (
    select revision_id, entity_id, property_id, value_id, timestamp, new_value->>0 as rank
    from value_change
    where change_target = 'rank' and property_id not in (-1, -2) -- description and labels don't have ranks
),
intervals as (
    select
        revision_id as revision_id_from,
        lead(revision_id) over (
            partition by entity_id, property_id, value_id
            order by timestamp, revision_id
        ) as revision_id_to,
        entity_id, property_id, value_id, rank,
        timestamp as valid_from,
        lead(timestamp) over (
            partition by entity_id, property_id, value_id
            order by timestamp, revision_id
        ) as valid_to
    from rank_changes
)
select *
from intervals
where rank is not null;       

create index idx_statement_rank_intervals_ent_prop_val_vf
    on statement_rank_intervals (entity_id, property_id, value_id, valid_from);

analyze statement_rank_intervals;