-- Update the Database schema from 2.5.0 to 2.6.0
-- Add ability to track equipment usage (in minutes)

ALTER TABLE equipment ADD service_minutes INT UNSIGNED DEFAULT 0 NOT NULL;

DROP PROCEDURE IF EXISTS log_access_completion;

DELIMITER $
CREATE PROCEDURE log_access_completion(p_card_id INT UNSIGNED, p_equipment_id INT UNSIGNED)
	MODIFIES SQL DATA
BEGIN
	DECLARE l_charge_policy_id INT UNSIGNED;
	DECLARE l_use_start_timestamp TIMESTAMP;
	DECLARE l_use_duration INT UNSIGNED;

	-- log in case all else fails
	INSERT INTO log(event_type_id, card_id, equipment_id, time)
		VALUES (3, p_card_id, p_equipment_id, CURRENT_TIMESTAMP);

	-- figure out charges if need be
	SET l_charge_policy_id = (SELECT et.charge_policy_id FROM equipment AS e
								INNER JOIN equipment_types AS et ON et.id = e.type_id
								WHERE e.id = p_equipment_id);
	SET l_use_start_timestamp = (SELECT start_time FROM in_use
								WHERE equipment_id = p_equipment_id LIMIT 1);
	SET l_use_duration = TIMESTAMPDIFF(MINUTE, l_use_start_timestamp, NOW());

	-- update equipment with new usage minutes
	UPDATE equipment SET service_minutes = service_minutes + l_use_duration WHERE id = p_equipment_id;

	CASE l_charge_policy_id
		WHEN 3 THEN -- per use
			INSERT INTO charges(user_id, equipment_id, amount, charge_policy_id, charge_rate, charged_time)
				SELECT uxc.user_id, p_equipment_id, et.charge_rate, l_charge_policy_id, et.charge_rate, l_use_duration
					FROM equipment AS e
					INNER JOIN equipment_types AS et ON et.id = e.type_id
					INNER JOIN users_x_cards AS uxc
					WHERE e.id = p_equipment_id AND uxc.card_id = p_card_id;
		WHEN 4 THEN -- per minute
			INSERT INTO charges(user_id, equipment_id, amount, charge_policy_id, charge_rate, charged_time)
				SELECT uxc.user_id, p_equipment_id, et.charge_rate * l_use_duration, l_charge_policy_id, et.charge_rate, l_use_duration
					FROM equipment AS e
					INNER JOIN equipment_types AS et ON et.id = e.type_id
					INNER JOIN users_x_cards AS uxc
					WHERE e.id = p_equipment_id AND uxc.card_id = p_card_id;
		ELSE BEGIN END;
	END CASE;

	DELETE FROM in_use WHERE equipment_id = p_equipment_id;
END$
DELIMITER ;

INSERT INTO schema_versioning(version, comment) VALUES ("2.6.0", "Migration Complete");