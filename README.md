# LOOT Marketplace Framework

#### We are bringing blockchain gaming to the mainstream, providing a complete and viable solution to digitalizing assets in fast paced large scale commercial games without hindering on the end user.

#### At it's core we are targeting the gaming industry; allowing the trading of digitalized assets instantly and securely for the end user, through the utilization of the NEO blockchain, smart contracts and a front-running relaying network. 

#### Producers/developers can simply integrate with the network, registering their marketplace in the smart contract. They will then be able to leverage exclusive management rights to their assets, without needing to trust a third party. 

#### For more information or to get in contact with the team visit: http://www.loottoken.io/


## Wallet 

The LOOT wallet is a tool used to securely store game assets.
It provides the following functionality:

- Secure offline wallet creation and saving which includes NEP-2 support.
- Signing and sending transactions.
- Claiming and redeeming generated GAS.
- Viewing names, stats, descriptions and photos of registered marketplace assets.
- Viewing prices and balances of system assets and NEP-5 tokens.
- Tracking the 24 hour change of your balance and individual NEO assets.
- Full interaction with the LOOT Marketplace framework, including trading/buying/selling/removing/cancelling game assets.
- Two currently registered titles, LootClicker and Project: MEYSA with more to be announced soon.
- A network monitor for the framework in which all data is publicly queryable.

### Screenshots

![WALLET_1](https://s3.amazonaws.com/loottoken.io/Wallet_1.png)


![WALLET_2](https://s3.amazonaws.com/loottoken.io/Wallet_2.png)


![WALLET_4](https://s3.amazonaws.com/loottoken.io/Wallet_4.png)


### Download Links

#### Wallet release: TBA

- MacOS and Windows wallet builds have been given to NGD and NEL for review. 
- Upon completion, the download links and source code will be MIT licensed and placed in this repository.

#### WARNING: Mainnet is available, but please do not use this feature until the wallet code has been thoroughly tested and reviewed by a NGD and/or NEL member. Doing so beforehand could potentially result in a loss of funds. 

### Network Relaying

- Currently anyone will be able to relay a transaction through our wallet if they have the required transaction GAS cost.
- As transactions under 10 gas are currently free, incentives will be rolled out once testing is completed.
- An algorithm calculates the network fees in order to cover GAS costs dependent on several factors and in a manageable way with the utility token LOOT.
- Multiple mechanisms are in place to ensure relayed transactions do not fault under any circumstance.
- This will be explained in more detail in the whitepaper.

## Framework API - http://lootmarketplacenode.com:8090/

### Network Order Format

An order can be sent via a raw string in JSON format in the body of a POST request through the route  ```/add_order/``` to the public API with the following details of what an address would like to do.

NOTE: There is a 5 second timeout between orders for players to discourage spam before fees are introduced.


```
{
  "operation":       # The operation the maker of this order wants to perform. 
                      "put_offer,buy_offer,cancel_offer,give_item,remove_item,withdraw"
  "address":         # The address of the maker of the order.
  "taker_address":   # Optionally the address the maker of the order specifies.
  "tokens":          # How many tokens the originator is spending.
  "item_id":         # The id of the item the maker is performing the operation on. 
  "marketplace":     # Which marketplace this is occurring on.
  "signature":       # The signature of this signed order.
  "public_key":      # The public key of the maker.
  "salt":            # A unique GUID so that this order may only occur once.
}
```



### Framework API Routes

#### POST /add_order/
- Add an order to the framework, if in the proper format and allowed to occur these changes will be reflected immediately.

Example: http://lootmarketplacenode.com:8090/add_order/

Request body:
```
{
  "operation": "buy_item",
  "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y",
  "taker_address": "",
  "tokens": 2,   
  "item_id": 101,         
  "marketplace": "LootClicker"  
  "signature": "8932a691788c2ac8489812a291523ad2ee878306a0f9dc15e676f7f3c01eff00f8a294ee6804f44a1c15e0762de128cdd2f60525f4e199c7e630732dbb7ef9ce"      
  "public_key":  "02c190a00cb234adf6763e5f6ac5a45cc0eaaf442f881f7e329359625dcc9bc671",
  "salt": "307128a7e69547a59cb7bc49a198759a"       
}
```

Response body:
```
{
    "result": True,
    "error_code": 0
}
```

#### GET /marketplaces/get
- Query a list of registered games/marketplaces.

Example: http://lootmarketplacenode.com:8090/marketplaces/get


Response body:

```
{
    "marketplaces": [
        "LootClicker",
        "Project_MEYSA"
    ]
}
```


#### GET /market/get/[marketplace]
- Query a list of items being sold on a marketplace.

Example: http://lootmarketplacenode.com:8090/market/get/LootClicker

Response body:
```
{
    "marketplace": "LootClicker",
    "offers": [
        "{\"marketplace\": \"LootClicker\", \"offer_id\": \"07db509b3a1e4e0ab990519055328a1c\", \"address\": \"AdRpcifzm36LGRcVhfeC2YmsoPARNLTQ3j\", \"item_id\": 735, \"price\": 112345678, \"tag\": \"\", \"type\": \"Shotgun\", \"slug\": 2017, \"name\": \"TCR-37 Skyforged Cinder\", \"rarity\": 2, \"description\": \"A cruel looking design favoured by those who like to intimidate their comrades as well as their foes.\", \"misc\": \"20 DPC / 4.16 CD\\n-2 % DPS / 2 % IDLE / 2 % XP / 2 % Bounty\"}",
        "{\"marketplace\": \"LootClicker\", \"offer_id\": \"7378e1bbbf4749e5abf058bb1a922769\", \"address\": \"AdRpcifzm36LGRcVhfeC2YmsoPARNLTQ3j\", \"item_id\": 737, \"price\": 543520000000, \"tag\": \"\", \"type\": \"Pistol\", \"slug\": 2004, \"name\": \"R9-360 Atomic Prism\", \"rarity\": 4, \"description\": \"This laser hand-cannon has several aftermarket parts, cobbled together from all sorts of other models.\", \"misc\": \"18 DPC / .03 CD\\n-6 % DPS / 2 % IDLE / 2 % XP / 2 % Bounty\"}"
    ]
}
```

#### GET /market/get_offer/[offer_id]
- Query a specific offer by its offer_id value.

Example: http://lootmarketplacenode.com:8090/market/get/LootClicker

Response body:
```
{
    "offer": "{\"marketplace\": \"LootClicker\", \"offer_id\": \"07db509b3a1e4e0ab990519055328a1c\", \"address\": \"AdRpcifzm36LGRcVhfeC2YmsoPARNLTQ3j\", \"item_id\": 735, \"price\": 112345678, \"tag\": \"\", \"type\": \"Shotgun\", \"slug\": 2017, \"name\": \"TCR-37 Skyforged Cinder\", \"rarity\": 2, \"description\": \"A cruel looking design favoured by those who like to intimidate their comrades as well as their foes.\", \"misc\": \"20 DPC / 4.16 CD\\n-2 % DPS / 2 % IDLE / 2 % XP / 2 % Bounty\"}"
}
```


#### GET /inventory/[marketplace]/[address]
- Query the inventory of an address on a specific marketplace.

Example: http://lootmarketplacenode.com:8090/inventory/Project_MEYSA/AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr

Response body:
```
{
    "address": "AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr",
    "inventory": [
        100000,
        100002,
        100003,
        100005,
        100000,
        100002,
        100003,
        100005,
        100004
    ]
}
```

#### GET /item/[marketplace]/[id]
- Query the details of an item on a specific marketplace with its id value.

Example: http://lootmarketplacenode.com:8090/item/Project_MEYSA/100000

Response body:
```
{
    "id": 100000,
    "marketplace": "Project_MEYSA",
    "name": "SunSpring, the Fatherly",
    "description": "SunSpring is a hippie who truly believes he has “transcended” the island, becoming some kind of deity and that everyone on the island is his child.",
    "slug": 1,
    "type": "Skin",
    "misc": "",
    "rarity": 5
}
```


#### GET /history/address/[address]
- Query the framework network history of an address.

Example: http://lootmarketplacenode.com:8090/history/address/AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y

Response body:
```
{
    "address": "AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr",
    "history": [
        "{\n    \"address\": \"AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr\",\n    \"address_to\": \"\",\n    \"item_id\": 100004,\n    \"marketplace\": \"Project_MEYSA\",\n    \"name\": null,\n    \"offer_id\": null,\n    \"operation\": \"cancel_offer\",\n    \"salt\": null,\n    \"slug\": -1,\n    \"timestamp\": 1534112429.046384,\n    \"tokens\": 100000000000\n}",
        "{\n    \"address\": \"AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr\",\n    \"address_to\": \"\",\n    \"item_id\": 100004,\n    \"marketplace\": \"Project_MEYSA\",\n    \"name\": null,\n    \"offer_id\": null,\n    \"operation\": \"put_offer\",\n    \"salt\": null,\n    \"slug\": -1,\n    \"timestamp\": 1534112387.7050304,\n    \"tokens\": 100000000000\n}"
    ]
}
```


#### GET /history/marketplace/[marketplace]
- Query the framework network history of marketplace.

Example: http://lootmarketplacenode.com:8090/history/all/LootClicker

Response body:

Response body:
```
{
    "history": [
        "{\n    \"address\": \"AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr\",\n    \"address_to\": \"\",\n    \"item_id\": 100004,\n    \"marketplace\": \"Project_MEYSA\",\n    \"name\": \"Penny\",\n    \"offer_id\": \"572ed69f4188468cab3c112e523ff8a0\",\n    \"operation\": \"cancel_offer\",\n    \"salt\": \"e6a6bde631974c8d84e0494c386cb541\",\n    \"slug\": 3,\n    \"timestamp\": 1534112429.046384,\n    \"tokens\": 100000000000\n}",
        "{\n    \"address\": \"AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr\",\n    \"address_to\": \"\",\n    \"item_id\": 100004,\n    \"marketplace\": \"Project_MEYSA\",\n    \"name\": \"Penny\",\n    \"offer_id\": null,\n    \"operation\": \"put_offer\",\n    \"salt\": \"572ed69f4188468cab3c112e523ff8a0\",\n    \"slug\": 3,\n    \"timestamp\": 1534112387.7050304,\n    \"tokens\": 100000000000\n}"
    ]
}
```

#### GET /history/all/[number]
- Query the complete marketplace history with the specified number of values being returned, ordered by the newest first.

Example: http://lootmarketplacenode.com:8090/history/all/2

Response body:
```
{
    "history": [
        "{\n    \"address\": \"AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr\",\n    \"address_to\": \"\",\n    \"item_id\": 100004,\n    \"marketplace\": \"Project_MEYSA\",\n    \"name\": \"Penny\",\n    \"offer_id\": \"572ed69f4188468cab3c112e523ff8a0\",\n    \"operation\": \"cancel_offer\",\n    \"salt\": \"e6a6bde631974c8d84e0494c386cb541\",\n    \"slug\": 3,\n    \"timestamp\": 1534112429.046384,\n    \"tokens\": 100000000000\n}",
        "{\n    \"address\": \"AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr\",\n    \"address_to\": \"\",\n    \"item_id\": 100004,\n    \"marketplace\": \"Project_MEYSA\",\n    \"name\": \"Penny\",\n    \"offer_id\": null,\n    \"operation\": \"put_offer\",\n    \"salt\": \"572ed69f4188468cab3c112e523ff8a0\",\n    \"slug\": 3,\n    \"timestamp\": 1534112387.7050304,\n    \"tokens\": 100000000000\n}"
    ]
}
```

#### GET /wallet/[address]
- Query the amount of LOOT an address has deposited into the smart contract.

Example: http://lootmarketplacenode.com:8090/wallet/AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr

Response body:

```
{
    "balance": 3300000000
}
```



#### GET /wallet/withdrawing/[address]
- Query the amount of LOOT an address is currently withdrawing from the smart contract.

Example: http://lootmarketplacenode.com:8090/wallet/withdrawing/AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr

Response body:

```
{
    "balance": 0
}
```

#### GET /network/information
- Query any additional network information of the framework.

Example: http://lootmarketplacenode.com:8090/network/information

Response body:

```
{
    "relayers": 1,
    "transactions_pending": 0,
    "payout_ratio": 0,
    "fee_ratio": 0
}
```

### Utility Routes

#### POST /wallets/create
- Create a NEP-2 key and address with the password specified in the request body.
- Integrated titles can use this as a way to give a wallet to their players without needing any heavier frameworks involved.

Example: http://lootmarketplacenode.com:8090/wallets/create

Request body:
```
{
  "password":"password123"
}
```

Response body:
```
{
    "address": "AYjiaSfysSxsxATzH2gRiGWTvmLfmu65Us",
    "nep2_key": "6PYKNmC7Dzoq1JXVjjkrGzwdKS7N2U2vkKtP1G8rUXLHm4d16HQ1RAXMzN"
}
```


#### POST /send_raw_tx/
- For convenience, post a raw transaction to the NEO node with the highest synced block height.

Example: http://lootmarketplacenode.com:8090/send_raw_tx/

Request body:
```
d1013d511423ba2703c53263e8d6e522dc32203339dcd8eee9044c6f6f7453c10a676976655f6974656d73676916b6583fad1b36b25476896cbdd2c9645070b1000000000000000000000001414015abcfca9ed66738f71feef13d90cfb58ac7e97745b6a0c089c1d25cf3dd1f8c464c28eb92c04eefa4507e17db1ecf87aacbdecbf37aef516c9914ad1ffdde9c2321031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac
```

Response body:
```
{
    "result": false
}
```
#### GET /get_node_height
- Get the height of the blockchain this marketplace node is listening for events on.

Example: http://lootmarketplacenode.com:8090/get_node_height

Response body:

```
{
    "height": "137116"
}
```

### Decentralized Game Mode Routes

#### GET /battle_royale/logs
- Query the log of all the smart contract events caught from ```Notify```.
- Games can query this to understand exactly what was resolved in the smart contract.

Example: http://lootmarketplacenode.com:8090/battle_royale/logs

Response body:

```
{
    "logs": [
        "{\n    \"address\": \"AaeGQWooqqyTe65GGNcsEU9Nn7VArY64Ne\",\n    \"address_vs\": null,\n    \"event_code\": \"697\",\n    \"message\": 0,\n    \"result\": true,\n    \"round\": 0,\n    \"salt\": \"36ab7595059844c6a436c9260c6494af\",\n    \"type\": \"BR_sign_up\",\n    \"zone\": 0\n}",
        "{\n    \"address\": \"AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr\",\n    \"address_vs\": null,\n    \"event_code\": \"697\",\n    \"message\": 0,\n    \"result\": true,\n    \"round\": 0,\n    \"salt\": \"3f20ade7726148e98bdc828c21ba1210\",\n    \"type\": \"BR_create\",\n    \"zone\": 0\n}"
    ]
}
```

#### GET /battle_royale/leaderboard/[event_code]
- Query the leaderboard of an event royale match.

Example: http://lootmarketplacenode.com:8090/battle_royale/leaderboard/697

Response body:
```
{
    "leaderboard": "["AaeGQWooqqyTe65GGNcsEU9Nn7VArY64Ne","AM1px3B3GWNP3sXZTdcHYhpKzDL8xrg3Mr"]"
}
```



## LootClicker (ALPHA) - Play at http://www.lootclicker.online

- For more information and screenshots please visit http://www.loottoken.io/lootclicker


![GAME_1](https://s3.amazonaws.com/loottoken.io/lc_1.png)


![GAME_2](https://s3.amazonaws.com/loottoken.io/idle2.jpg)


![GAME_3](https://s3.amazonaws.com/loottoken.io/combat_demo1.jpg)



##### NOTE: As we are in alpha testing, only whitelisted emails will be able to register and login. You can sign up for this on our website at LootToken.io

#### Overview
- LootClicker is our proof of concept MMO casual clicker game. 
- Players can earn items from crates, or in decentralized game modes. 
- The centralized aspect of game logic itself is managed by an authoritative server, every action which may effect the in game economy and value of assets is verified and accepted by the server, this will attempt to remove all cheating from the game to properly simulate an in game economy.
- The in game equipable assets are all integrated into the framework and therefore registered on the NEO blockchain.

#### Game Features

The following features are currently working:

- Singleplayer mode in which the player can fight enemies and defeat powerful bosses to advance stages.
- Offline bounty (soft currency) and experience generation that is claimed upon login, this is scaled dependent on your idle damage and stage.
- Find rare gems in combat that can be spent to perform actions such as creating guilds, starting events and rerolling your class.
- In game digital assets all are given stats and/or abilities according to their rarity along with unique sounds and effects.
- There are 7 weapon classes to use, equipping a weapon class with give you an additional active skill to use in combat.
- Unlock mercenaries with bounty in single player mode that will increase damage output.
- At level 100+ you can "Server Hop". You will gain passive bonuses and be able to unlock active/passive skills, but in turn will be stripped of your current rank, currency and stage.
- At higher levels you may choose and unlock from 3 talent classes; beserker, specialist and lawless. These each have their own unique active and passive skills. 
- Join a guild, with up to 50 members to chat, rank up, and complete timed events to earn rewards.
- Daily rewards can be collected on a login streak over 30 days.
- Unlock over 100 achievements which yield unique rewards and titles.
- Enter our first decentralized game mode "Blockchain Royale", all logic is resolved on the blockchain in a smart contract.
- A friends list, global online chat with channels and private messaging.
- View the gear and stats of any other player.
- Equip pets, cosmetics and weapons to use in battle.
- Leaderboards for guilds and players.
- Progress is never lost, and bound to your account/blockchain.
- A full functioning in game marketplace has been integrated to showcase how assets can be sold, bought and traded on the marketplace framework.

#### Accessing LootClicker items in the wallet
- You may register an account with a pre-existing private key, or else a new one will be created for you.
  - You can copy this private key, and with it log into the wallet with the first option on the menu.
  - In the "Settings", you can click "Save Wallet" to enable easy access into the wallet where you can access your items.
- Any items in your wallet are cross synced with an integrated game, so purchased marketplace items in the wallet will be available for use in LootClicker without an effort on the players part.

### Next release - Patch 1.1

We aim to have the following released by the next patch as we transition into open beta.

- Fixing any residual alpha bugs.
- Standalone builds for mac/pc. 
- Add new cosmetics, mercenaries and items.
- Perfect the in game scaling algorithms for the best player experience.
- Support for WebGL uploading profile pictures.
- Android/Mac build begins.

## Decentralized Game Modes

### Blockchain Royale

![BR_1](https://s3.amazonaws.com/loottoken.io/br_mode.jpg)

As part of the NEO-Game competition, we wanted to showcase the potential of what a smart contract is capable of. We have decided to release our first decentralized game mode based on the popular "Battle Royale" gamemode. 

- Every single action of this game mode is decided and resolved inside the smart contract and output through ```Notify``` events which are relayed to the game including:

  - Movement 
  - Map boundaries
  - Random in game events 
  - Timeouts
  - Looting and fighting 
  - Giving out rewards to winners

- Important game information which is caught from the ```Notify``` events is publicly queryable through the API calls listed.


#### Phases

##### Creation: 
Contract call: ``` BR_create [UniqueGameID,Address,Marketplace,Items] ```
- A marketplace owner may create an event, and pass in x rewards, which will be given to the last x players of the match.

##### Sign Up: 
Contract call: ``` BR_sign_up [UniqueGameID,Address] ```
- Players may sign up to the event, this registers them into the event in the smart contract itself.

##### Start: 
Contract call: ``` BR_start [UniqueGameID,Address] ```
- The owner of the event can start the event, each round has a timeout period, in which players who do not move will be eliminated.

##### Round 0 (Landing):
Contract call: ``` BR_choose_initial_zone [UniqueGameID,Address,Zone] ```

- The player can "spawn" in, choosing a zone to initially be on, if it is in the constraints of the grid created.

##### Round 1+: 
Contract call: ``` BR_do_action [UniqueGameID,Address,Action,Direction] ```

A registered and not yet eliminated address may do one of the following recognized actions each round:
  - "Move","Hide","Loot". 
    - If a player is hiding, they have the advantage, 60% chance to win.
    - If a player is looting, they can find untradeable in game items in their current zone, although this will yield a disadvantage, a 40% chance to win.
    - A player can move to a square, 40 % chance to win.
    - If percentages are the same, it will go to a 50-50 roll.
  - To encourage movement and unique gameplay, after round 4, every round a new side of the grid map will be randomly chosen to be destroyed. This event is notified and will be seen in game.

##### Finish Round:
Contract call: ``` BR_finish_round [UniqueGameID] ```

- This can be called by anyone and will resolve the round on the condition that; all the players have made an action for the round, or the round has timed out. 
- If the event is complete, being there is <= 1 player, the smart contract will automatically finish the event and give the prizes to the x amount players as specified in the creation stage.


## Acknowledgements

Without the following this project would not be possible.
We offer a sincere thank you and hope we will be able to give something back.

- NEO
- NGD
- NEL
- CoZ
- NEO-python
- NEO-lux 
- @metachris
- @localhuman

