create table small_table as
select v.entity_id, v.property_id, v.value_id, v.timestamp, v.action, v.label, v.change_type, r.user_type,
       (action = 'CREATE'
        or (action = 'UPDATE' and (label = 'value_update'
                                   or change_type = 'property_value_update'))) as is_overall_activity
from value_change_to_keep v join revision r on v.revision_id = r.revision_id
where change_target = ''
  and is_reverted = 0 and reversion = 0
  and property_id not in (-1, -2)
  and action != 'DELETE'
order by v.entity_id, v.property_id, v.value_id, v.timestamp; 

create index on small_table(entity_id, property_id, value_id, timestamp);
analyze small_table;