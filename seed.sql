-- ============================================================
-- Talent Bridge — Database Setup & Seed
-- Run this in MySQL after creating the talent_bridge DB
-- ============================================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS talent_bridge
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE talent_bridge;

-- ── Sample Job Listings ────────────────────────────────────
INSERT INTO job_listings (title, company, location, job_type, salary_min, salary_max, description, requirements)
VALUES
  ('Flutter Developer', 'TechCorp Solutions', 'Remote', 'Full-time', 80000, 120000,
   'Build beautiful cross-platform mobile apps using Flutter and Dart. Work with a talented team on cutting-edge products.',
   'Flutter, Dart, REST APIs, Git, 2+ years experience'),

  ('Backend Engineer (Python)', 'DataFlow Inc', 'Yaoundé, Cameroon', 'Full-time', 60000, 90000,
   'Design and build scalable backend services using Python Flask/FastAPI and MySQL.',
   'Python, Flask, MySQL, Docker, REST APIs, 2+ years'),

  ('AI/ML Engineer', 'NeuralLabs Africa', 'Remote', 'Full-time', 100000, 150000,
   'Develop and deploy machine learning models for real-world applications across Africa.',
   'Python, TensorFlow, PyTorch, scikit-learn, 3+ years'),

  ('UI/UX Designer', 'Pixel Studio', 'Douala, Cameroon', 'Part-time', 40000, 60000,
   'Create stunning user interfaces and experiences for mobile and web products.',
   'Figma, Adobe XD, Prototyping, User Research, 1+ year'),

  ('DevOps Engineer', 'CloudBase Technologies', 'Remote', 'Full-time', 90000, 130000,
   'Manage cloud infrastructure and CI/CD pipelines for high-availability systems.',
   'AWS, Docker, Kubernetes, Terraform, Linux, 3+ years'),

  ('Software Engineering Intern', 'StartupX Cameroon', 'Yaoundé, Cameroon', 'Internship', NULL, NULL,
   'Gain hands-on experience building real software products. Mentorship provided.',
   'Any programming language, enthusiasm to learn, student or recent graduate'),

  ('Data Analyst', 'Insights Corp', 'Remote', 'Contract', 50000, 70000,
   'Analyze large datasets to provide actionable business insights using SQL and Python.',
   'SQL, Python, Power BI or Tableau, Statistics, 1+ year'),

  ('Mobile App Developer (React Native)', 'AppFactory', 'Remote', 'Full-time', 70000, 100000,
   'Develop cross-platform mobile applications using React Native.',
   'React Native, JavaScript, TypeScript, Redux, 2+ years'),

  ('Cybersecurity Analyst', 'SecureNet Africa', 'Douala, Cameroon', 'Full-time', 75000, 110000,
   'Protect digital assets and respond to security incidents for enterprise clients.',
   'Network Security, Penetration Testing, SIEM, 2+ years, relevant certifications'),

  ('Full-Stack Developer', 'FinTech Solutions', 'Yaoundé, Cameroon', 'Full-time', 65000, 95000,
   'Build end-to-end financial technology solutions for the African market.',
   'Node.js or Python, React or Vue, MySQL or PostgreSQL, 2+ years');
