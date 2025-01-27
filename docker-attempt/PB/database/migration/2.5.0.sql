-- Add function to database to calculate the account balance for user given a card_id
--	assigned tot he user.

DROP FUNCTION IF EXISTS get_user_balance_for_card;

-- use a stored function to get the balance for the user presenting a card
DELIMITER $
CREATE FUNCTION get_user_balance_for_card(p_card_id INT UNSIGNED)
	RETURNS DECIMAL(10,2)
	READS SQL DATA
BEGIN
	DECLARE l_total_payments DECIMAL(10,2);
	DECLARE l_total_charges DECIMAL(10,2);

	SET l_total_payments = (SELECT sum(p.amount) FROM payments AS p
							INNER JOIN users_x_cards AS u ON u.user_id = p.user_id
							WHERE u.card_id = p_card_id);
	SET l_total_charges = (SELECT sum(c.amount) FROM charges AS c
							INNER JOIN users_x_cards AS u ON u.user_id = c.user_id
							WHERE u.card_id = p_card_id);
	RETURN IFNULL(l_total_payments, 0.0) - IFNULL(l_total_charges, 0.0);
END$
DELIMITER ;

INSERT INTO schema_versioning(version, comment) VALUES ("2.5.0", "Migration Complete");