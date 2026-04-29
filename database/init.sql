-- FOF管理平台数据库初始化脚本

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `fof` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `fof`;

-- 注意：表结构由SQLAlchemy自动创建
-- 这里只做一些初始化配置

SET FOREIGN_KEY_CHECKS = 1;
