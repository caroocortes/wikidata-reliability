create table sampled_changes_static_props as
with prev_revision_timestamp as (
    select 
        revision_id, 
        timestamp,
        user_type,
        user_id,
        username,
        comment,
        lag(timestamp) over (partition by entity_id order by timestamp) as prev_edit_on_entity
    from revision
)
select 
    r.revision_id, 
    v.entity_id,
    v.entity_label,
    v.property_id,
    v.property_label,
    value_id,
    old_value,
    new_value,
    old_datatype,
    new_datatype,
    change_target,
    action,
    r.timestamp,
    year_month,
    year,
    label,
    change_type,
    user_type,
    username,
    user_id,
    comment,
    et.first_revision_timestamp as entity_first_revision_timestamp,
    r.prev_edit_on_entity
from 
    sampled_entities_static_props pt 
    join value_change v on pt.entity_id = v.entity_id and pt.property_id = v.property_id
    join entity_stats et on et.entity_id = v.entity_id
    join prev_revision_timestamp r on r.revision_id = v.revision_id
where v.change_target = '' and action != 'DELETE';