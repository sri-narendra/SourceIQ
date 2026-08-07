-- seed/001_demo_user.sql
-- Demo user for local development. Password: Password@123 (bcrypt hash below).

INSERT INTO users (id, name, email, password_hash, role, plan)
VALUES (
    gen_random_uuid(),
    'Narendra',
    'narendra@example.com',
    '$2b$12$KIXfZP9CXZ4Kc1Z0K5Cqwe0KqXkM0aK8VjzFQ6H8i7ZgW1bLvP3sG',
    'user',
    'free'
) ON CONFLICT (email) DO NOTHING;