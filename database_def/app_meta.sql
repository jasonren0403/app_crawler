CREATE TABLE `app_meta` (
  `name` varchar(255) DEFAULT NULL,
  `store` varchar(255) NOT NULL,
  `score` decimal(5,2) DEFAULT NULL,
  `description` mediumtext,
  `public_time` int(10) DEFAULT NULL,
  `category` varchar(255) DEFAULT NULL,
  `developer` varchar(255) DEFAULT NULL,
  `download_times` int(10) DEFAULT NULL,
  `review_times` int(10) DEFAULT NULL,
  `app_id` varchar(255) NOT NULL,
  `md5` char(32) DEFAULT NULL,
  PRIMARY KEY (`app_id`,`store`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci