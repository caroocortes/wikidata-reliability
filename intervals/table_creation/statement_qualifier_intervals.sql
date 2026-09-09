SET work_mem = '4GB';
create table statement_qualifier_intervals as
with qual_changes as (
    select 
		revision_id, 
		entity_id, 
		property_id, 
		value_id, 
		qual_property_id,
		value_hash,
		new_value->>0 as qual_value,
		timestamp,
		action                                  
    from qualifier_change_to_keep
),
intervals as (
	select
		revision_id as revision_id_from,
		lead(revision_id) over (
	        partition by entity_id, property_id, value_id, qual_property_id, value_hash
	        order by timestamp, revision_id
	    ) as revision_id_to,
	    entity_id, property_id, value_id, qual_property_id, value_hash, qual_value,
	    timestamp as valid_from,
	    lead(timestamp) over (
	        partition by entity_id, property_id, value_id, qual_property_id, value_hash
	        order by timestamp, revision_id
	    ) as valid_to
	from qual_changes
)
select * 
from intervals
where qual_value is not NULL; 

create index idx_qual_intervals
    on statement_qualifier_intervals (entity_id, property_id, value_id, valid_from);