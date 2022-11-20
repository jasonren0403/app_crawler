CREATE TABLE `app_comment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_id` varchar(255) DEFAULT NULL,
  `review_id` varchar(255) DEFAULT NULL,
  `store` varchar(255) DEFAULT NULL,
  `user` varchar(255) DEFAULT NULL,
  `score` int(10) DEFAULT NULL,
  `time` int(10) DEFAULT NULL,
  `content` mediumtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=166348 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci