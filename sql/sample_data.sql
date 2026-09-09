create table sampled_changes_static_props as
select 
    r.revision_id, 
    v.entity_id,
    v.entity_label,
    v.property_id,
    v.property_label,
    v.value_id,
    v.old_value,
    v.new_value,
    v.old_datatype,
    v.new_datatype,
    v.change_target,
    v.action,
    r.timestamp,
    r.year_month,
    r.year,
    v.label,
	v.is_reverted,
	v.reversion,
    v.change_type,
    r.user_type,
    r.username,
    r.user_id,
    r.comment,
    et.first_revision_timestamp as entity_first_revision_timestamp,
    v.citation_needed
from 
    (select * from entities_static_props where entity_id not in (4115189, 112795079, 15397819, 13406268, 17339402, 16943273) limit 100000) pt 
    join value_change v on pt.entity_id = v.entity_id and pt.property_id = v.property_id
    join entity_stats et on et.entity_id = v.entity_id
    join revision r on r.revision_id = v.revision_id
where v.change_target = '';

create table sampled_references_static_props as
select 
	ir.revision_id, 
	ir.entity_id,
	ir.entity_label,
	rc.property_id,
	rc.property_label,
	rc.value_id,
	rc.ref_property_id,
	rc.ref_property_label,
	rc.ref_hash,
	rc.value_hash,
	rc.old_value,
	rc.new_value,
	rc.old_datatype,
	rc.new_datatype,
	rc.change_target,
	rc.action,
	ir.timestamp,
	ir.year_month,
	ir.year,
	rc.label,
	ir.user_type,
	ir.username,
	ir.user_id,
	ir.comment
from sampled_changes_static_props ir join reference_change rc on ir.entity_id = rc.entity_id and ir.property_id = rc.property_id;

create table entity_information as 
select 
	entity_age
from value_change v
where 
	v.change_target = ''
	and 
	v.property_id in (select distinct property_id
						from sampled_changes_static_props);


alter table sampled_changes_static
add column entity_type text default '';

create index idx_sample_static_entity_id on sampled_changes_static(entity_id);

update sampled_changes_static s
set entity_type = et.entity_type
from entity_types_exploded et
where s.entity_id = et.entity_id;