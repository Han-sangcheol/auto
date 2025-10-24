-- CleonAI Trading Platform 시드 데이터

-- 테스트 사용자 생성 (비밀번호: test1234, bcrypt 해시)
INSERT INTO users (username, email, hashed_password, is_active, is_superuser)
VALUES 
    ('admin', 'admin@cleonai.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7UxzDZNRqS', TRUE, TRUE),
    ('testuser', 'test@cleonai.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7UxzDZNRqS', TRUE, FALSE)
ON CONFLICT DO NOTHING;

-- 테스트 계좌 생성
INSERT INTO accounts (user_id, broker, account_no, account_name, account_type, initial_balance, current_balance, is_active)
VALUES 
    (1, 'kiwoom', '8123456789', '모의투자 계좌', 'simulation', 10000000, 10000000, TRUE),
    (2, 'mock', '9999999999', 'Mock 테스트 계좌', 'simulation', 5000000, 5000000, TRUE)
ON CONFLICT DO NOTHING;

-- 기본 전략 설정
INSERT INTO strategies (account_id, name, type, parameters, is_active, priority)
VALUES 
    (1, '이동평균 크로스오버', 'ma_cross', '{"short_period": 5, "long_period": 20}', TRUE, 1),
    (1, 'RSI 전략', 'rsi', '{"period": 14, "oversold": 30, "overbought": 70}', TRUE, 2),
    (1, 'MACD 전략', 'macd', '{"fast": 12, "slow": 26, "signal": 9}', TRUE, 3),
    (1, '급등주 감지', 'surge', '{"min_change_rate": 5.0, "min_volume_ratio": 2.0, "cooldown_minutes": 30}', TRUE, 4)
ON CONFLICT DO NOTHING;

-- 샘플 시세 데이터 (최근 1주일, 삼성전자 예시)
-- 실제 운영에서는 백엔드에서 실시간으로 수집
INSERT INTO market_data (timestamp, stock_code, open_price, high_price, low_price, close_price, volume, trade_value, change_rate)
SELECT 
    (CURRENT_TIMESTAMP - (interval '1 day' * generate_series(7, 0, -1)))::timestamp,
    '005930',
    75000 + (random() * 2000 - 1000)::int,
    76000 + (random() * 2000)::int,
    74000 - (random() * 1000)::int,
    75000 + (random() * 2000 - 1000)::int,
    (10000000 + random() * 5000000)::bigint,
    (750000000000 + random() * 100000000000)::bigint,
    (random() * 4 - 2)::decimal(10,2)
ON CONFLICT DO NOTHING;

-- 시스템 로그 샘플
INSERT INTO system_logs (level, source, message, details)
VALUES 
    ('INFO', 'backend', 'Database initialized successfully', '{"version": "1.0.0"}'),
    ('INFO', 'engine', 'Trading engine started', '{"mode": "simulation"}')
ON CONFLICT DO NOTHING;

