SET work_mem = '5GB';
create table statement_reference_intervals as
with ref_changes as (
    select revision_id, entity_id, property_id, value_id,
           ref_hash,  
           jsonb_object_agg(ref_property_id, new_value->>0) as ref_values,
           timestamp,
           action                                  
    from reference_change_to_keep
    group by revision_id, entity_id, property_id, value_id, ref_hash, timestamp, action
),
intervals as (
    select
        revision_id as revision_id_from,
        lead(revision_id) over (
            partition by entity_id, property_id, value_id, ref_hash
            order by timestamp, revision_id
        ) as revision_id_to,
        entity_id, property_id, value_id, ref_hash, ref_values,
        timestamp as valid_from,
        lead(timestamp) over (
            partition by entity_id, property_id, value_id, ref_hash
            order by timestamp, revision_id
        ) as valid_to
    from ref_changes
)
select *
from intervals
where ref_values is not null; 

create index idx_ref_intervals
    on statement_reference_intervals (entity_id, property_id, value_id, valid_from);