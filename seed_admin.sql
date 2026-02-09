INSERT INTO public."user" (email, password_hash, full_name, user_role_id, is_active, created_at, updated_at) 
VALUES ('admin@sistema.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'Administrador', 1, true, NOW(), NOW())
ON CONFLICT (email) DO NOTHING;
