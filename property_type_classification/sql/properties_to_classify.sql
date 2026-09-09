create table properties as 
select 
	plwd.property_id, 
	plwd.property_label, 
	padun.property_data_type,
	padun.aliases,
	padun.property_description,
	padun.frequency_update,
	padun.frequency_update_label,
	padun.has_characteristic_num_id
from property_labels_with_deleted plwd 
	left join 
	properties_alias_desc_update_freq_numeric_id padun on plwd.property_id = padun.property_id;

alter table properties
add column is_id_property int default 0;

-- if they don't have this statement put it as false
update properties 
set has_characteristic_num_id = coalesce(has_characteristic_num_id, false);

update properties p
set is_id_property = 1
where
	-- either has <p, has characteristic, numeric id>
    has_characteristic_num_id = true
	or
	property_data_type = 'ExternalId'
	or
	(
		property_label ~ '\yID\y'
		and (
			translate(property_description, 'аеорсіѕ', 'aeopcis') ilike '%identif%' -- identifier(s), identifying
			or translate(property_description, 'аеорсіѕ', 'aeopcis') ~ '\yIDs?\y'          -- word-boundary ID or IDs
			or translate(property_description, 'аеорсіѕ', 'aeopcis') ~ '\ycode\y'
			or coalesce(translate(aliases, 'аеорсіѕ', 'aeopcis'), '') ilike '%identif%'
			or coalesce(translate(aliases, 'аеорсіѕ', 'aeopcis'), '') ~ '\yIDs?\y'
			or coalesce(translate(aliases, 'аеорсіѕ', 'aeopcis'), '') ~ '\ycode\y' -- also check for code properties
		)
	);

-- Exclude deleted properties (as of June 2025)
alter table properties
add column was_deleted int default 0;

update properties
set was_deleted = 1
where property_data_type IS NULL;

-- Properties to exclude since they are IDs
alter table properties
add column to_exclude int default 0;

update properties
set to_exclude = 1
where (was_deleted = 1 and property_label ~ '\yID\y')or is_id_property = 1;

alter table properties
add column property_type text default '';

update properties
set property_type = 'irregular'
where frequency_update_label = 'sometimes changes';

update properties
set property_type = 'regular'
where frequency_update_label = 'continuously changes';

update properties
set property_type = 'static'
where frequency_update_label = 'never changes';

create table properties_to_classify as
select * 
from properties
where to_exclude = 0;

-- remove description adn label since they are not really "properties"
delete from properties_to_classify
where property_id in (-1, -2);