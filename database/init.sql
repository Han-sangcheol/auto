-- CleonAI Trading Platform 데이터베이스 초기화 스크립트

-- TimescaleDB 확장 활성화
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 계좌 테이블
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    broker VARCHAR(50) NOT NULL,  -- 'kiwoom', 'mock' 등
    account_no VARCHAR(50) NOT NULL,
    account_name VARCHAR(100),
    account_type VARCHAR(20) NOT NULL,  -- 'simulation', 'real'
    initial_balance BIGINT NOT NULL DEFAULT 0,
    current_balance BIGINT NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(broker, account_no)
);

-- 포지션 테이블 (현재 보유 종목)
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    avg_price INTEGER NOT NULL CHECK (avg_price > 0),
    current_price INTEGER NOT NULL DEFAULT 0,
    profit_loss BIGINT DEFAULT 0,
    profit_loss_percent DECIMAL(10, 2) DEFAULT 0,
    entry_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, stock_code)
);

-- 주문 테이블
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    order_type VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    price_type VARCHAR(20) NOT NULL,  -- 'market', 'limit'
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'filled', 'partially_filled', 'cancelled', 'rejected'
    filled_quantity INTEGER DEFAULT 0,
    filled_price INTEGER,
    strategy_name VARCHAR(100),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 거래 내역 테이블
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    trade_type VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    total_amount BIGINT NOT NULL,
    fee INTEGER DEFAULT 0,
    tax INTEGER DEFAULT 0,
    profit_loss BIGINT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 전략 설정 테이블
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'ma_cross', 'rsi', 'macd', 'surge', 'multi'
    parameters JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, name)
);

-- 급등주 감지 기록 테이블
CREATE TABLE IF NOT EXISTS surge_detections (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    detection_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    price INTEGER NOT NULL,
    change_rate DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    volume_ratio DECIMAL(10, 2) NOT NULL,
    trade_value BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'detected',  -- 'detected', 'approved', 'rejected', 'executed'
    approved_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE
);

-- 시계열 데이터 테이블 (시세 데이터)
CREATE TABLE IF NOT EXISTS market_data (
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    open_price INTEGER NOT NULL,
    high_price INTEGER NOT NULL,
    low_price INTEGER NOT NULL,
    close_price INTEGER NOT NULL,
    volume BIGINT NOT NULL,
    trade_value BIGINT,
    change_rate DECIMAL(10, 2),
    PRIMARY KEY (timestamp, stock_code)
);

-- TimescaleDB 하이퍼테이블 생성
SELECT create_hypertable('market_data', 'timestamp', if_not_exists => TRUE);

-- 로그 테이블
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    source VARCHAR(50) NOT NULL,  -- 'backend', 'engine', 'frontend'
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_account_id ON positions(account_id);
CREATE INDEX IF NOT EXISTS idx_orders_account_id ON orders(account_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_trades_account_id ON trades(account_id);
CREATE INDEX IF NOT EXISTS idx_trades_executed_at ON trades(executed_at);
CREATE INDEX IF NOT EXISTS idx_strategies_account_id ON strategies(account_id);
CREATE INDEX IF NOT EXISTS idx_surge_detections_stock_code ON surge_detections(stock_code);
CREATE INDEX IF NOT EXISTS idx_surge_detections_status ON surge_detections(status);
CREATE INDEX IF NOT EXISTS idx_market_data_stock_code ON market_data(stock_code, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at DESC);

-- 업데이트 시간 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 초기 데이터 확인
COMMENT ON DATABASE trading_db IS 'CleonAI Trading Platform Database';

