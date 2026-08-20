CREATE TABLE `saved_collection_members` (
	`id` int AUTO_INCREMENT NOT NULL,
	`collectionId` int NOT NULL,
	`offerId` int NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `saved_collection_members_id` PRIMARY KEY(`id`),
	CONSTRAINT `saved_collection_members_collection_offer_unique` UNIQUE(`collectionId`,`offerId`)
);
--> statement-breakpoint
CREATE TABLE `saved_collections` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`clientId` varchar(96) NOT NULL,
	`name` varchar(42) NOT NULL,
	`clientCreatedAt` timestamp NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `saved_collections_id` PRIMARY KEY(`id`),
	CONSTRAINT `saved_collections_user_client_unique` UNIQUE(`userId`,`clientId`)
);
