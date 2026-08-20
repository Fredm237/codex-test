CREATE TABLE `price_alerts` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`offerId` int NOT NULL,
	`productName` varchar(500) NOT NULL,
	`threshold` decimal(12,2) NOT NULL,
	`currency` varchar(3) NOT NULL,
	`status` enum('active','paused') NOT NULL DEFAULT 'active',
	`clientCreatedAt` timestamp NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `price_alerts_id` PRIMARY KEY(`id`),
	CONSTRAINT `price_alerts_user_offer_unique` UNIQUE(`userId`,`offerId`)
);
--> statement-breakpoint
CREATE TABLE `push_devices` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`expoToken` varchar(255) NOT NULL,
	`platform` enum('ios','android') NOT NULL,
	`permission` enum('granted','denied') NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `push_devices_id` PRIMARY KEY(`id`),
	CONSTRAINT `push_devices_token_unique` UNIQUE(`expoToken`)
);
