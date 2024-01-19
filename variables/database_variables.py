vacancies_table = "my_vacancies"

users_table = "users"
vacancy_links_table = "vacancy_links"
message_list_cash_table = "messages_cash"

users_table_create_query = f"CREATE TABLE IF NOT EXISTS {users_table} (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_user_id INT NOT NULL UNIQUE)"
vacancy_links_create_query = f"CREATE TABLE IF NOT EXISTS {vacancy_links_table} (id INTEGER PRIMARY KEY AUTOINCREMENT, link TEXT UNIQUE, seen BOOLEAN, rejected BOOLEAN, applied BOOLEAN, source_from TEXT, telegram_user_id INTEGER, FOREIGN KEY(telegram_user_id) REFERENCES users(telegram_user_id))"
message_list_cash_create_query = f"CREATE TABLE IF NOT EXISTS {message_list_cash_table} (id INTEGER PRIMARY KEY AUTOINCREMENT, message_id INT, message BLOB)"

vacancy_links_all_fields = ['id', 'link', "seen", "rejected", "applied", "telegram_user_id"]