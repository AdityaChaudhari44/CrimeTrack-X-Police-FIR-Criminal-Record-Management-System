-- ═══════════════════════════════════════════════════════════════
--  CrimeTrack-X  |  Database Schema
--  Police FIR & Criminal Record Management System
--  MySQL 8.0+
-- ═══════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS crimetrack_x
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE crimetrack_x;

-- ───────────────────────────────────────────────────────────────
--  1. USERS  (authentication accounts)
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)     NOT NULL UNIQUE,
    password_hash VARCHAR(255)    NOT NULL,
    role          ENUM('admin','officer') NOT NULL DEFAULT 'officer',
    is_active     TINYINT(1)      NOT NULL DEFAULT 1,
    last_login    DATETIME,
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role     (role)
) ENGINE=InnoDB;

-- ───────────────────────────────────────────────────────────────
--  2. OFFICERS
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS officers (
    officer_id     INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    user_id        INT UNSIGNED    UNIQUE,          -- linked login account
    badge_number   VARCHAR(20)     NOT NULL UNIQUE,
    full_name      VARCHAR(100)    NOT NULL,
    `rank`         VARCHAR(50)     NOT NULL,
    department     VARCHAR(100),
    phone          VARCHAR(15),
    email          VARCHAR(100),
    station        VARCHAR(100),
    date_joined    DATE,
    is_active      TINYINT(1)      NOT NULL DEFAULT 1,
    created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_badge  (badge_number),
    INDEX idx_name   (full_name)
) ENGINE=InnoDB;

-- ───────────────────────────────────────────────────────────────
--  3. CRIMINALS
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS criminals (
    criminal_id   INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(100)    NOT NULL,
    alias         VARCHAR(100),
    dob           DATE,
    gender        ENUM('Male','Female','Other'),
    nationality   VARCHAR(50)     DEFAULT 'Indian',
    address       TEXT,
    phone         VARCHAR(15),
    photo_path    VARCHAR(255),
    id_proof_type VARCHAR(50),
    id_proof_no   VARCHAR(50),
    blood_group   VARCHAR(5),
    physical_desc TEXT,
    is_wanted     TINYINT(1)      NOT NULL DEFAULT 0,
    arrest_count  INT UNSIGNED    NOT NULL DEFAULT 0,
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name    (full_name),
    INDEX idx_wanted  (is_wanted),
    INDEX idx_alias   (alias)
) ENGINE=InnoDB;

-- ───────────────────────────────────────────────────────────────
--  4. FIRs  (First Information Reports)
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS firs (
    fir_id          INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    fir_number      VARCHAR(30)     NOT NULL UNIQUE,   -- e.g. FIR-2024-000001
    complainant     VARCHAR(100)    NOT NULL,
    complainant_ph  VARCHAR(15),
    incident_date   DATE            NOT NULL,
    incident_time   TIME,
    location        TEXT            NOT NULL,
    offense_type    VARCHAR(100)    NOT NULL,
    ipc_sections    VARCHAR(255),
    description     TEXT,
    status          ENUM('Registered','Under Investigation','Charge-Sheeted',
                         'Closed','Disposed') NOT NULL DEFAULT 'Registered',
    officer_id      INT UNSIGNED,
    criminal_id     INT UNSIGNED,
    registered_by   INT UNSIGNED    NOT NULL,          -- user_id
    registered_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id)    REFERENCES officers(officer_id)  ON DELETE SET NULL,
    FOREIGN KEY (criminal_id)   REFERENCES criminals(criminal_id) ON DELETE SET NULL,
    FOREIGN KEY (registered_by) REFERENCES users(user_id),
    INDEX idx_fir_number  (fir_number),
    INDEX idx_status      (status),
    INDEX idx_incident    (incident_date),
    INDEX idx_offense     (offense_type)
) ENGINE=InnoDB;

-- ───────────────────────────────────────────────────────────────
--  5. CASES
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cases (
    case_id         INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    case_number     VARCHAR(30)     NOT NULL UNIQUE,
    fir_id          INT UNSIGNED    NOT NULL,
    title           VARCHAR(200)    NOT NULL,
    status          ENUM('Open','Pending','Under Investigation',
                         'Closed','Cold') NOT NULL DEFAULT 'Open',
    priority        ENUM('Low','Medium','High','Critical') DEFAULT 'Medium',
    assigned_to     INT UNSIGNED,                      -- officer_id
    court_date      DATE,
    verdict         TEXT,
    opened_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at       DATETIME,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (fir_id)       REFERENCES firs(fir_id)           ON DELETE CASCADE,
    FOREIGN KEY (assigned_to)  REFERENCES officers(officer_id)   ON DELETE SET NULL,
    INDEX idx_case_number (case_number),
    INDEX idx_status      (status),
    INDEX idx_priority    (priority)
) ENGINE=InnoDB;

-- ───────────────────────────────────────────────────────────────
--  6. INVESTIGATION NOTES
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS investigation_notes (
    note_id     INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    case_id     INT UNSIGNED    NOT NULL,
    officer_id  INT UNSIGNED,
    note_text   TEXT            NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id)    REFERENCES cases(case_id)           ON DELETE CASCADE,
    FOREIGN KEY (officer_id) REFERENCES officers(officer_id)     ON DELETE SET NULL,
    INDEX idx_case (case_id)
) ENGINE=InnoDB;

-- ───────────────────────────────────────────────────────────────
--  7. EVIDENCE
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id   INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    case_id       INT UNSIGNED    NOT NULL,
    evidence_type VARCHAR(100)    NOT NULL,
    description   TEXT,
    location      VARCHAR(255),
    collected_by  INT UNSIGNED,
    collected_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status        ENUM('Collected','In Lab','Processed','Archived') DEFAULT 'Collected',
    FOREIGN KEY (case_id)      REFERENCES cases(case_id)       ON DELETE CASCADE,
    FOREIGN KEY (collected_by) REFERENCES officers(officer_id) ON DELETE SET NULL,
    INDEX idx_case (case_id)
) ENGINE=InnoDB;

-- ───────────────────────────────────────────────────────────────
--  8. AUDIT LOGS
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id      INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED,
    action      VARCHAR(200)    NOT NULL,
    table_name  VARCHAR(50),
    record_id   INT UNSIGNED,
    details     TEXT,
    ip_address  VARCHAR(45),
    logged_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_user   (user_id),
    INDEX idx_action (action),
    INDEX idx_time   (logged_at)
) ENGINE=InnoDB;

-- ═══════════════════════════════════════════════════════════════
--  SEED DATA  –  default admin + sample records
-- ═══════════════════════════════════════════════════════════════

-- Default admin  (password: Admin@123)
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$2b$12$3ldW3DxyvR0gva2e.HjXEOVlCy277et03IrWJn7gkpX3fiTHkGXwW', 'admin');
-- Note: run scripts/seed_admin.py to regenerate hash with your bcrypt version

-- Sample officers
INSERT INTO users (username, password_hash, role) VALUES
('officer_raj',   '$2b$12$3ldW3DxyvR0gva2e.HjXEOVlCy277et03IrWJn7gkpX3fiTHkGXwW', 'officer'),
('officer_priya', '$2b$12$3ldW3DxyvR0gva2e.HjXEOVlCy277et03IrWJn7gkpX3fiTHkGXwW', 'officer');

INSERT INTO officers (user_id, badge_number, full_name, `rank`, department, phone, station, date_joined) VALUES
(2, 'MH-001', 'Rajesh Kumar',  'Inspector',     'Crime Branch', '9876543210', 'Central Station', '2018-05-10'),
(3, 'MH-002', 'Priya Sharma',  'Sub-Inspector', 'Cyber Crime',  '9876543211', 'East Station',    '2020-03-15');

-- Sample criminals
INSERT INTO criminals (full_name, alias, dob, gender, nationality, address, is_wanted, arrest_count) VALUES
('Vikram Tiwari',  'Black Viper', '1985-07-22', 'Male',   'Indian', '12 Shivaji Nagar, Mumbai', 1, 3),
('Sunita Desai',   'Ghost Lady',  '1990-01-11', 'Female', 'Indian', '45 MG Road, Pune',         0, 1),
('Rajan Mehta',    'The Hawk',    '1978-11-30', 'Male',   'Indian', '8 Civil Lines, Delhi',      1, 5);

-- Sample FIRs
INSERT INTO firs (fir_number, complainant, complainant_ph, incident_date, incident_time, location,
                  offense_type, ipc_sections, description, status, officer_id, criminal_id, registered_by) VALUES
('FIR-2024-000001', 'Amit Patel',   '9000000001', '2024-01-15', '22:30:00',
 'MG Road, Pune', 'Robbery', '392, 397',
 'Complainant was robbed at knifepoint near MG Road junction.',
 'Under Investigation', 1, 1, 1),

('FIR-2024-000002', 'Neeta Joshi',  '9000000002', '2024-02-20', '14:00:00',
 'Cyber Cafe, Baner', 'Cyber Fraud', '420, 66C IT Act',
 'Victim received a phishing call and lost Rs 50,000.',
 'Charge-Sheeted', 2, 2, 2),

('FIR-2024-000003', 'Suresh Gupta', '9000000003', '2024-03-05', '08:15:00',
 'Highway NH-4, Lonavala', 'Vehicle Theft', '379',
 'Truck hijacked on highway. Driver assaulted.',
 'Registered', 1, 3, 1);

-- Sample cases
INSERT INTO cases (case_number, fir_id, title, status, priority, assigned_to) VALUES
('CASE-2024-000001', 1, 'MG Road Robbery Investigation',    'Under Investigation', 'High',     1),
('CASE-2024-000002', 2, 'Baner Cyber Fraud Prosecution',    'Pending',             'Medium',   2),
('CASE-2024-000003', 3, 'NH-4 Truck Hijacking – Cold Lead', 'Open',                'Critical', 1);

-- Sample investigation notes
INSERT INTO investigation_notes (case_id, officer_id, note_text) VALUES
(1, 1, 'CCTV footage retrieved from nearby ATM. Suspect matches description of Vikram Tiwari.'),
(1, 1, 'Witness statements collected. Two eyewitnesses identified suspect.'),
(2, 2, 'IP address traced to a cybercafe in Baner. Warrant obtained for records.');

-- Sample evidence
INSERT INTO evidence (case_id, evidence_type, description, location, collected_by, status) VALUES
(1, 'CCTV Recording', 'ATM camera footage 22:15–22:45 on 15-Jan-2024', 'Evidence Room A, Locker 3', 1, 'Processed'),
(1, 'Weapon',         'Knife recovered near crime scene (tagged EV-001)',  'Forensic Lab',              1, 'In Lab'),
(2, 'Digital Evidence','Phishing URL logs and call records',               'Cyber Cell Server',          2, 'Processed');
