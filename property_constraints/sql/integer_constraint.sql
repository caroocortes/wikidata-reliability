alter table value_change_to_keep
add column violates_integer_constraint int default 0;

create index idx_value_change_to_keep_new_dt on value_change_to_keep(new_datatype);
analyze value_change_to_keep;

update value_change_to_keep v
set violates_integer_constraint = 1
from integer_constraint rc
where 
	rc.property_id = v.property_id and 
	(
		-- not a numeric value
		(new_datatype != 'quantity') or
		-- it's numeric and if I cast the value to int, it's different from itself -> it has a comma
		(new_value->>0 != new_value->>0::int )
	);