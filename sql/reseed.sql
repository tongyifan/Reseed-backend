-- phpMyAdmin SQL Dump
-- version 4.9.0.1
-- https://www.phpmyadmin.net/
--
-- 主机： 127.0.0.1
-- 生成日期： 2019-10-21 21:38:09
-- 服务器版本： 8.0.16
-- PHP 版本： 7.3.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 数据库： `reseed`
--

-- --------------------------------------------------------

--
-- 表的结构 `error_torrents`
--

CREATE TABLE `error_torrents` (
  `id` int(11) NOT NULL,
  `tid` int(11) NOT NULL,
  `site` varchar(20) NOT NULL,
  `reason` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- 表的结构 `historys`
--

CREATE TABLE `historys` (
  `id` int(11) NOT NULL,
  `time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `uid` int(11) NOT NULL,
  `hash` char(32) NOT NULL,
  `result` json NOT NULL,
  `ip` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- 表的结构 `sites`
--

CREATE TABLE `sites` (
  `site` varchar(10) NOT NULL,
  `base_url` varchar(30) NOT NULL,
  `download_page` varchar(50) NOT NULL DEFAULT 'download.php?id={}',
  `rss_page` varchar(255) DEFAULT 'torrentrss.php?rows=50&passkey={}&linktype=dl',
  `torrents_page` varchar(50) NOT NULL DEFAULT 'torrents.php?incldead=0&page={}',
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `passkey` varchar(32) NOT NULL,
  `cookies` mediumtext NOT NULL,
  `skip_page` int(11) NOT NULL DEFAULT '0',
  `show` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- 表的结构 `torrents`
--

CREATE TABLE `torrents` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `files` longtext,
  `length` bigint(20) NOT NULL,
  `sites_existed` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `added_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- 表的结构 `torrent_records`
--

CREATE TABLE `torrent_records` (
  `id` int(11) NOT NULL,
  `tid` int(11) NOT NULL,
  `sid` int(11) NOT NULL,
  `site` varchar(15) NOT NULL,
  `added_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- 表的结构 `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `passhash` varchar(100) NOT NULL,
  `added_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `tjupt_id` int(11) NOT NULL DEFAULT '0',
  `ourbits_id` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- 转储表的索引
--

--
-- 表的索引 `error_torrents`
--
ALTER TABLE `error_torrents`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `error_torrents_pk` (`tid`,`site`);

--
-- 表的索引 `historys`
--
ALTER TABLE `historys`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `historys_id_uindex` (`id`);

--
-- 表的索引 `sites`
--
ALTER TABLE `sites`
  ADD PRIMARY KEY (`site`),
  ADD UNIQUE KEY `sites_site_uindex` (`site`);

--
-- 表的索引 `torrents`
--
ALTER TABLE `torrents`
  ADD PRIMARY KEY (`id`),
  ADD KEY `torrents_name_index` (`name`(250));

--
-- 表的索引 `torrent_records`
--
ALTER TABLE `torrent_records`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `torrent_records_id_uindex` (`id`),
  ADD UNIQUE KEY `torrent_records_sid_site_uindex` (`sid`,`site`),
  ADD KEY `tid` (`tid`);

--
-- 表的索引 `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `users_id_uindex` (`id`),
  ADD UNIQUE KEY `users_username_uindex` (`username`);

--
-- 在导出的表使用AUTO_INCREMENT
--

--
-- 使用表AUTO_INCREMENT `error_torrents`
--
ALTER TABLE `error_torrents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `historys`
--
ALTER TABLE `historys`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `torrents`
--
ALTER TABLE `torrents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `torrent_records`
--
ALTER TABLE `torrent_records`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
