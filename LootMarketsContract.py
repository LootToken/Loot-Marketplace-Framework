"""
===== LootMarketExchange =====

MIT License

Copyright 2018 LOOT Token Inc. & Warped Gaming LLC

Author: @poli
Email: chris.luke.poli@gmail.com

This smart contract enables the creation of marketplaces for games, that is, it
integrates a storage system for items on the NEO blockchain as "digital assets" where
they are tradeable for the NEP-5 asset LOOT tied to a fiat value. A marketplace is registered
with an owner, who has exclusive permissions to invoke the operations on this marketplace.

For our proof of concept game LootClicker, this contract includes its first decentralized game mode 
inspired by the "Battle Royale" genre of games. 
All aspects of game logic are decided in this contract and it aims to show what a NEO smart contract is capable of.
"""

from boa.builtins import concat, list, range, take, substr, verify_signature, sha256, hash160, hash256
from boa.interop.System.ExecutionEngine import GetScriptContainer, GetExecutingScriptHash, GetCallingScriptHash,GetEntryScriptHash
from boa.interop.Neo.Transaction import Transaction, TransactionInput, GetReferences, GetOutputs, GetUnspentCoins,GetAttributes, GetInputs
from boa.interop.Neo.Output import GetValue, GetAssetId, GetScriptHash
from boa.interop.Neo.Attribute import TransactionAttribute
from boa.interop.Neo.TriggerType import Application, Verification
from boa.interop.Neo.Storage import Get, Put, Delete, GetContext
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Blockchain import GetHeight, ShowAllContracts, GetContract, GetHeader
from boa.interop.Neo.Runtime import Notify, Serialize, Deserialize, CheckWitness, GetTrigger
from boa.interop.Neo.App import RegisterAppCall, DynamicAppCall
from boa.interop.Neo.Header import Header

# region Marketplace Variables

# Wallet hash of the owner of the contract.
contract_owner = b'9|3W[\xec\r\xe7\xd8\x03\xd8\xe9\x15\xe1\x933\x92P\xfc\xb0'

# Hash of the NEP-5 loot token contract.
LootTokenHash = b'i\x9b\xf7\x17L\xd7\x0f\xbe\xea\xe4\xc5R\xe7\xb0\xddX\x8a\x89\xca\xcb'

# Register the hash of the NEP-5 LOOT token contract to enable cross contract operations.
LootContract = RegisterAppCall('cbca898a58ddb0e752c5e4eabe0fd74c17f79b69', 'operation', 'args')

# Storage keys
contract_state_key = b'State'  # Stores the state of the contract.
inventory_key = b'Inventory'  # The inventory of an address.
marketplace_key = b'Marketplace'  # The owner of a marketplace
offers_key = b'Offers'  # All the offers available on a marketplace.
order_key = b'Order'  # Mark an order as complete so it is not completed.

# Fee variables
feeFactor = 10000
MAX_FEE = 10000000

# Contract States
TERMINATED = b'\x01'  # Anyone may do any core operations without owners permission e.g. emergency button.
PENDING = b'\x02'  # The contract needs to be initialized before trading is opened.
ACTIVE = b'\03'  # All operations are active and managed by the LOOT Marketplace framework.

# endregion


# region Decentralized Game variables

# Stores the rewards that competition owner has placed.
battle_royale_rewards_key = b'BattleRoyaleRewards'
# A list of the destroyed zones.
battle_royale_destroyed_zones_key = b'BattleRoyaleGas'
# The zone which is marked to be destroyed.
battle_royale_marked_destroyed_zone_key = b"BRMarkedZone"
# For more information about every entrant.
battle_royale_entrant_key = b'BattleRoyaleInformation'
# A list of players so we can easily iterate through the remaining players.
battle_royale_current_players_key = b'BattleRoyaleCurrentPlayers'
# The details of the event.
battle_royale_details_key = b'BattleRoyaleDetails'
# Leaderboard results of the event.
battle_royale_event_results_key = b'BREventResults'

# Zones start being destroyed at round 4.
ROUND_DESTROYED_ZONES_GENERATE = 4

# 5% chance to find loot per "loot" roll each round, increases + 5% each round.
BR_CHANCE_TO_FIND_LOOT = 5
BR_CHANCE_INCREASE_PER_ROUND = 5
# The round will timeout after 10 blocks.
BR_ROUND_TIMEOUT = 10
BR_UNTRADEABLE_REWARDS = ["Gem", "Ammo", "Crate", "Bounty"]

# endregion


def Main(operation, args):
    """
    The entry point for the smart contract.
    :param operation: str The operation to invoke.
    :param args: list A list of arguments for the operation.
    :return:
        bytearray: The result of the operation.    """

    print("LootMarketExchange: Version 2.5: Testnet")
    trigger = GetTrigger()
    if trigger == Application():

        # ========= Marketplace Operations ==========

        # Fill the order on the blockchain.
        if operation == "exchange":
            if len(args) == 14:
                marketplace = args[0]
                marketplace_owner_address = args[1]
                marketplace_owner_signature = args[2]
                marketplace_owner_public_key = args[3]
                originator_address = args[4]
                originator_signature = args[5]
                originator_public_key = args[6]
                taker_address = args[7]
                taker_signature = args[8]
                taker_public_key = args[9]
                item_id = args[10]
                price = args[11]
                originator_order_salt = args[12]
                taker_order_salt = args[13]

                operation_result = exchange(marketplace, marketplace_owner_address, marketplace_owner_signature,
                                            marketplace_owner_public_key, originator_address, originator_signature,
                                            originator_public_key, taker_address, taker_signature, taker_public_key,
                                            originator_order_salt, taker_order_salt, item_id, price)

                payload = ["exchange", originator_order_salt, marketplace, operation_result]
                Notify(payload)

                return operation_result

        if operation == "trade":
            # Trade must have an terminated implementation so users will never lose access to their assets.
            if get_contract_state() == TERMINATED:
                if len(args) == 4:
                    marketplace = args[0]
                    originator_address = args[1]
                    taker_address = args[2]
                    item_id = args[3]

                    if not CheckWitness(originator_address):
                        return False

                    operation_result = trade(marketplace, originator_address, taker_address, item_id)
                    return operation_result

            if len(args) == 10:
                marketplace = args[0]
                originator_address = args[1]
                taker_address = args[2]
                item_id = args[3]
                originator_signature = args[4]
                originator_public_key = args[5]
                marketplace_owner_address = args[6]
                marketplace_owner_signature = args[7]
                marketplace_owner_public_key = args[8]
                originator_order_salt = args[9]

                operation_result = trade_verified(marketplace, originator_address, taker_address, item_id,
                                                  marketplace_owner_address, marketplace_owner_signature,
                                                  marketplace_owner_public_key, originator_signature,
                                                  originator_public_key, originator_order_salt)
                transaction_details = ["trade", originator_order_salt, marketplace, operation_result]
                Notify(transaction_details)

                return operation_result

        if operation == "give_item":
            # Marketplace owners must be able to still give items without the framework.
            if get_contract_state() == TERMINATED:
                if len(args) == 4:
                    marketplace = args[0]
                    originator_address = args[1]
                    taker_address = args[2]
                    item_id = args[3]

                    if not CheckWitness(originator_address):
                        return False
                    if not is_marketplace_owner(marketplace, originator_address):
                        return False

                    operation_result = trade(marketplace, originator_address, taker_address, item_id)
                    return operation_result

            if len(args) == 7:
                marketplace = args[0]
                address_to = args[1]
                item_id = args[2]
                marketplace_owner = args[3]
                marketplace_owner_signature = args[4]
                marketplace_owner_public_key = args[5]
                originator_order_salt = args[6]

                operation_result = give_item_verified(marketplace, address_to, item_id, marketplace_owner,
                                                      marketplace_owner_signature, marketplace_owner_public_key,
                                                      originator_order_salt)
                payload = ["give_item", originator_order_salt, marketplace, operation_result]
                Notify(payload)
                return operation_result

        if operation == "give_items":
            marketplace = args[0]
            address_to = args[1]
            marketplace_owner = args[2]
            marketplace_owner_signature = args[3]
            marketplace_owner_public_key = args[4]
            originator_order_salt = args[5]

            # Remove verification arguments, leaving the item ids to give an address.
            for i in range(0, 6):
                args.remove(0)

            operation_result = give_items_verified(marketplace, address_to, marketplace_owner,
                                                   marketplace_owner_signature, marketplace_owner_public_key, args)
            payload = ["give_items", originator_order_salt, marketplace, operation_result]
            Notify(payload)
            return operation_result

        if operation == "remove_item":
            # Remove item must have a terminated implementation so users can still access their assets.
            if get_contract_state() == TERMINATED:
                if len(args) == 3:
                    marketplace = args[0]
                    originator_address = args[1]
                    item_id = args[3]

                    if CheckWitness(originator_address):
                        return False
                    operation_result = remove_item(marketplace, originator_address, item_id)
                    return operation_result

            if len(args) == 9:
                marketplace = args[0]
                originator_address = args[1]
                item_id = args[2]
                originator_signature = args[3]
                originator_public_key = args[4]
                marketplace_owner_address = args[5]
                marketplace_owner_signature = args[6]
                marketplace_owner_public_key = args[7]
                originator_order_salt = args[8]

                operation_result = remove_item_verified(marketplace, originator_address, item_id,
                                                        originator_order_salt, marketplace_owner_address
                                                        , marketplace_owner_signature, marketplace_owner_public_key,
                                                        originator_signature, originator_public_key)
                payload = ["remove_item", originator_order_salt, marketplace, operation_result]
                Notify(payload)
                return operation_result

        # Queries

        if operation == "get_inventory":
            if len(args) == 2:
                marketplace = args[0]
                address = args[1]
                inventory_s = get_inventory(marketplace, address)
                if inventory_s == b'':
                    inventory = []
                else:
                    inventory = Deserialize(inventory_s)

                payload = ["get_inventory", marketplace, address, inventory]
                Notify(payload)
                return True

        if operation == "marketplace_owner":
            if len(args) == 2:
                marketplace = args[0]
                address = args[1]
                result = is_marketplace_owner(marketplace, address)

                payload = ["marketplace_owner", marketplace, address, result]
                Notify(payload)
                return result

        # ========= Administration, Crowdsale & NEP-5 Specific Operations ==========

        if operation == "receiving":
            if len(args) == 3:
                # Get the script hash of the address calling this.
                caller = GetCallingScriptHash()

                # Must be from the LOOT nep-5 contract.
                if caller != LootTokenHash:
                    return False

                return handle_deposit(args)

        if operation == "withdraw":
            # Users will be able to withdraw their funds in a terminated state.
            if get_contract_state() == TERMINATED:
                if len(args) == 2:
                    originator_address = args[0]
                    amount = args[1]
                    my_hash = GetExecutingScriptHash()

                    if not CheckWitness(originator_address):
                        return False

                    operation_result = withdrawal(my_hash, originator_address, amount)
                    return operation_result

            if len(args) == 8:
                originator_address = args[0]
                tokens = args[1]
                originator_signature = args[2]
                originator_public_key = args[3]
                owner_address = args[4]
                owner_signature = args[5]
                owner_public_key = args[6]
                originator_order_salt = args[7]

                my_hash = GetExecutingScriptHash()

                if withdrawal_verified(my_hash, originator_address, tokens, originator_signature, originator_public_key,
                                       owner_address, owner_signature, owner_public_key, originator_order_salt):
                    order_complete(originator_order_salt)
                    payload = ["withdraw", originator_order_salt, originator_address, tokens]
                    Notify(payload)
                    return True

                return False

        if operation == "transfer":
            if len(args) == 9:
                originator_address = args[0]
                taker_address = args[1]
                tokens = args[2]
                originator_signature = args[3]
                originator_public_key = args[4]
                marketplace_owner_address = args[5]
                marketplace_owner_signature = args[6]
                marketplace_owner_public_key = args[7]
                originator_order_salt = args[8]

                operation_result = transfer_token_verified(originator_address, taker_address, tokens,
                                                           originator_signature, originator_public_key,
                                                           marketplace_owner_address, marketplace_owner_signature,
                                                           marketplace_owner_public_key, originator_order_salt)

                transaction_details = ["transfer", originator_order_salt, operation_result]
                Notify(transaction_details)
                return operation_result

        if operation == "add_owner_wallet":
            marketplace = args[0]
            address = args[1]
            return add_owner_wallet(marketplace, address)

        if operation == "set_maker_fees":
            if len(args) == 2:
                marketplace = args[0]
                fee = args[1]
                return set_maker_fee(marketplace, fee)

        if operation == "set_taker_fees":
            if len(args) == 2:
                marketplace = args[0]
                fee = args[1]
                return set_taker_fee(marketplace, fee)

        if operation == "get_maker_fee":
            if len(args) == 1:
                marketplace = args[0]
                return get_maker_fee(marketplace)

        if operation == "get_taker_fee":
            if len(args) == 1:
                marketplace = args[0]
                return get_taker_fee(marketplace)

        # Query the LOOT balance of an address.
        if operation == "balance_of":
            if len(args) == 1:
                address = args[0]
                balance = balance_of(address)
                # Notify the API with the LOOT balance of the address.
                transaction_details = ["balance_of", address, balance]
                Notify(transaction_details)
                return balance

        # OWNER only
        if CheckWitness(contract_owner):

            # Register a new marketplace on the blockchain.
            if operation == "register_marketplace":
                if len(args) == 4:
                    marketplace = args[0]
                    address = args[1]
                    maker_fee = args[2]
                    taker_fee = args[3]
                    return register_marketplace(marketplace, address, maker_fee, taker_fee)

            if operation == "set_contract_state":
                contract_state = args[0]
                set_contract_state(contract_state)
                return True

        # State of the contract.
        if operation == "get_state":
            return get_contract_state()

        # ========= Decentralized Games ==========

        # Battle Royale

        if operation == "BR_create":
            # To start the event, the marketplace owner, uploads rewards and requirements.
            event_code = args[0]
            marketplace_owner_address = args[1]
            marketplace = args[2]

            # Remove the first 3 keyword args, the following should be items.
            for i in range(0, 3):
                args.remove(0)

            result = BR_create(event_code, marketplace, marketplace_owner_address, args)

            payload = ["BR", event_code, "BR_create", marketplace_owner_address, result]
            Notify(payload)

            return result

        if operation == "BR_sign_up":
            if len(args) == 2:
                event_code = args[0]
                address = args[1]

                result = BR_sign_up(event_code, address)
                details = ["BR", event_code, "BR_sign_up", address, result]
                Notify(details)

                return result

        if operation == "BR_start":
            if len(args) == 2:
                event_code = args[0]
                address = args[1]

                result = BR_start(event_code, address)

                details = ["BR", event_code, "BR_start", address, result]
                Notify(details)

                return result

        if operation == "BR_choose_initial_zone":
            if len(args) == 3:
                event_code = args[0]
                address = args[1]
                zone = args[2]

                # The first action which will be resolved the next round.
                return BR_choose_initial_grid_position(event_code, address, zone)

        if operation == "BR_do_action":
            if len(args) == 4:
                event_code = args[0]
                address = args[1]
                action = args[2]
                direction = args[3]

                return BR_do_action(event_code, address, action, direction)

        if operation == "BR_finish_round":
            if len(args) == 1:
                event_code = args[0]

                return BR_finish_round(event_code)

        if operation == "BR_get_leaderboard":

            if len(args) == 1:
                context = GetContext()

                event_code = args[0]
                leaderboard = get_BR_leaderboard(context, event_code)
                if leaderboard != b'':
                    leaderboard = Deserialize(leaderboard)
                else:
                    leaderboard = []
                payload = ["BR", event_code, 'leaderboard', leaderboard]
                Notify(payload)

                return True

        if operation == "BR_get_event_details":
            if len(args) == 1:
                context = GetContext()

                event_code = args[0]
                event_details = get_BR_event_details(context, event_code)
                payload = ["BR", event_code, "event_details", event_details]
                Notify(payload)

                return True

        return False

    # Owner will not be allowed to withdraw anything.
    if trigger == Verification():
        pass
        # check if the invoker is the owner of this contract
        # is_owner = CheckWitness(contract_owner)

        # If owner, proceed
        # if is_owner:
        #    return True

    return False


def exchange(marketplace, marketplace_owner_address, marketplace_owner_signature,
             marketplace_owner_public_key, originator_address, originator_signature,
             originator_public_key, taker_address, taker_signature, taker_public_key,
             originator_order_salt, taker_order_salt, item_id, price):
    """
    Verify the signatures of two parties and securely swap the item, and tokens between them.
    """

    if order_complete(originator_order_salt):
        print("ERROR! This transaction has already occurred!")
        return False

    if order_complete(taker_order_salt):
        print("ERROR! This transaction has already occurred!")
        return False

    originator_args = ["put_offer", marketplace, item_id, price, originator_order_salt]

    if not verify_order(originator_address, originator_signature, originator_public_key, originator_args):
        print("ERROR! originator has not signed the order")
        return False

    taker_args = ["buy_offer", marketplace, item_id, price, taker_order_salt]
    if not verify_order(taker_address, taker_signature, taker_public_key, taker_args):
        print("ERROR! Taker has not signed the order!")
        return False

    # A marketplace owner must verify so there are no jumps in the queue.
    marketplace_owner_args = ["exchange", marketplace, item_id, price, originator_address, taker_address]

    if not verify_order(marketplace_owner_address, marketplace_owner_signature, marketplace_owner_public_key,
                        marketplace_owner_args):
        print("ERROR! Marketplace owner has not signed the order!")
        return False

    if not trade(marketplace, originator_address, taker_address, item_id):
        print("ERROR! Items could not be transferred.")
        return False

    if not transfer_token(taker_address, originator_address, price):
        print("ERROR! Tokens could not be transferred.")
        return False

    # Set the orders as complete so they can only occur once.
    set_order_complete(originator_order_salt)
    set_order_complete(taker_order_salt)

    return True



def trade_verified(marketplace, originator_address, taker_address, item_id,
                   marketplace_owner_address, marketplace_owner_signature,
                   marketplace_owner_public_key, originator_signature,
                   originator_public_key, salt):
    """
    Transfer an item from an address, to an address on a marketplace.
    """

    if not is_marketplace_owner(marketplace, marketplace_owner_address):
        print("ERROR! Only a marketplace owner is allowed to give items.")
        return False

    if order_complete(salt):
        print("ERROR! This order has already occurred!")
        return False

    args = ["trade", marketplace, originator_address, taker_address, item_id, salt]

    if not verify_order(marketplace_owner_address, marketplace_owner_signature, marketplace_owner_public_key, args):
        print("ERROR! The marketplace owner has not permitted the transaction.")
        return False

    if not verify_order(originator_address, originator_signature, originator_public_key, args):
        print("ERROR! The address removing has not signed this!")
        return False

    if trade(marketplace, originator_address, taker_address, item_id):
        set_order_complete(salt)
        return True

    print("ERROR! Could not complete the trade")
    return False


def trade(marketplace, originator_address, taker_address, item_id):
    """
    Trade an item from one address to another, on a specific marketplace.
    """
    # If the item is being transferred to the same address, don't waste gas and return True.
    if originator_address == taker_address:
        return True

    # If the removal of the item from the address sending is successful, give the item to the address receiving.
    if remove_item(marketplace, originator_address, item_id):
        if give_item(marketplace, taker_address, item_id):
            return True




def give_item_verified(marketplace, taker_address, item_id,
                       owner_address, owner_signature,
                       owner_public_key, salt):
    """
    Give an item to an address on a specific marketplace, verified by a marketplace owner.
    """

    if not is_marketplace_owner(marketplace, owner_address):
        print("Only a marketplace owner is allowed to give items.")
        return False

    if order_complete(salt):
        print("This order has already occurred!")
        return False

    args = ["give_item", marketplace, taker_address, item_id, 0, salt]
    if not verify_order(owner_address, owner_signature, owner_public_key, args):
        print("A marketplace owner has not signed this order.")
        return False

    set_order_complete(salt)

    give_item(marketplace, taker_address, item_id)

    return True

def give_item(marketplace, taker_address, item_id):
    """
    Give an item to an address on a specific marketplace.
    """
    # Get the players inventory from storage.
    inventory_s = get_inventory(marketplace, taker_address)

    # If the address owns no items create a new list, else grab the pre-existing list and append the new item.
    if inventory_s == b'':
        inventory = [item_id]
    else:
        inventory = Deserialize(inventory_s)
        inventory.append(item_id)

    # Serialize and save the inventory back to the storage.
    inventory_s = Serialize(inventory)
    save_inventory(marketplace, taker_address, inventory_s)

    return True

def give_items_verified(marketplace, taker_address, item_id,
                        owner_address, owner_signature,
                        owner_public_key, salt, items):
    """
    Give many items at once.
    This can be useful for developers giving  their users many items at once.
    In game item bundles would not be efficient to send many verifiable items at once.
    With a cap of 16 parameters being passable to the smart contract,
    and the first 6 parameters being used for verification,
    it allows up to 10 items that are currently able to be given to a user at once.
    """
    if not is_marketplace_owner(marketplace, owner_address):
        print("ERROR! Only a marketplace owner is allowed to give items.")
        return False

    if order_complete(salt):
        print("ERROR! This order has already occurred!")
        return False

    args = ["give_items", marketplace, taker_address, item_id, 0, salt, items]
    if not verify_order(owner_address, owner_signature, owner_public_key, args):
        print("A marketplace owner has not signed this order.")
        return False

    inventory_s = get_inventory(marketplace, taker_address)

    # If the inventory has no items, create a new list, else get the pre-existing list.
    if inventory_s == b'':
        inventory = []
    else:
        inventory = Deserialize(inventory_s)

    # This method does not work if this print statement is removed.
    print("placeholder")
    for item in args:
        inventory.append(item)

    # Serialize and save the modified inventory back into storage.
    inventory_s = Serialize(inventory)
    save_inventory(marketplace, taker_address, inventory_s)

    set_order_complete(salt)

    return True



def remove_item_verified(marketplace, address, item_id, salt, owner_address,
                         owner_signature, owner_public_key, signature, public_key):
    """
    Remove an item from an address on a marketplace.
    """

    if not is_marketplace_owner(marketplace, owner_address):
        print("ERROR! Only a marketplace owner is allowed to give items.")
        return False

    if order_complete(salt):
        print("ERROR! This order has already occurred!")
        return False

    args = ["remove_item", marketplace, address, item_id, 0, salt]
    if not verify_order(owner_address, owner_signature, owner_public_key, args):
        print("ERROR! A marketplace owner has not signed this order.")
        return False

    owner_args = ["remove_item", marketplace, address, item_id, 0, salt]
    if not verify_order(address, signature, public_key, owner_args):
        print("ERROR! The address removing has not signed this!")
        return False

    if remove_item(marketplace, address, item_id):
        set_order_complete(salt)
        return True

    return False


def remove_item(marketplace, address, item_id):
    """
    Remove an item from an address on a specific marketplace.
    """
    inventory_s = get_inventory(marketplace, address)
    if inventory_s != b'':
        inventory = Deserialize(inventory_s)
        current_index = 0

        for item in inventory:
            if item == item_id:
                inventory.remove(current_index)
                inventory_s = Serialize(inventory)
                save_inventory(marketplace, address, inventory_s)
                return True
            current_index += 1

    return False


def verify_order(address, signature, public_key, args):
    """
    Verify that an order is properly signed by a signature and public key.
    We also ensure the public key can be recreated into the script hash
    so we know that it is the address that signed it.
    """

    message = ""
    for arg in args:
        message = concat(message, arg)

    # Create the script hash from the given public key, to verify the address.
    redeem_script = b'21' + public_key + b'ac'
    script_hash = hash160(redeem_script)

    # Must verify the address we are doing something for is the public key whom signed the order.
    if script_hash != address:
        print("ERROR! The public key does not match with the address who signed the order.")
        return False

    if not verify_signature(public_key, signature, message):
        print("ERROR! Signature has not signed the order.")
        return False

    return True


def get_contract_state():
    """Current state of the contract."""
    context = GetContext()
    state = Get(context, contract_state_key)
    return state


def set_contract_state(state):
    """ Set the state of the contract. """
    context = GetContext()
    Delete(context, contract_state_key)
    Put(context, contract_state_key, state)

    return True


def set_order_complete(salt):
    """ So an order is not repeated, user has signed a salt. """
    context = GetContext()
    key = concat(order_key, salt)
    Put(context, key, True)

    return True


def order_complete(salt):
    """ Check if an order has already been completed."""
    context = GetContext()
    key = concat(order_key, salt)
    exists = Get(context, key)
    if exists != b'':
        return True

    return False
    # return exists != b''


def increase_balance(address, amount):
    """
    Called on deposit to increase the amount of LOOT in storage of an address.
    """
    context = GetContext()

    # LOOT balance is mapped directly to an address
    key = address

    current_balance = Get(context, key)
    new_balance = current_balance + amount

    Put(context, key, new_balance)

    # Notify that address there deposit is complete
    evt = ["deposit", address, amount]
    Notify(evt)

    return True


def reduce_balance(address, amount):
    """
    Called on withdrawal, to reduce the amount of LOOT in storage of an address.
    """
    context = GetContext()
    if amount < 1:
        print("ERROR! Can only reduce a balance >= 1. ")
        return False

    # LOOT is mapped directly to address
    key = address

    current_balance = Get(context, key)
    new_balance = current_balance - amount

    if new_balance < 0:
        print("ERROR! Not enough balance to reduce!")
        return False

    if new_balance > 0:
        Put(context, key, new_balance)
    else:
        Delete(context, key)

    return True



def transfer_token_verified(originator_address, taker_address, tokens, originator_signature, originator_public_key,
                            owner_address, owner_signature, owner_public_key, salt):
    """
    Transfer tokens on the framework.

    Token transfers within this contract are only meant to be done for purchasing items with MTX.
    This must be allowed through by the contract owner.

    NOTE: Funds will always still be able to be withdrawn by a user back into the NEP-5 contract
    if the contract is in a terminated state.
    """

    if owner_address != contract_owner:
        print("ERROR! Address specified is not the contract owner.")
        return False

    if order_complete(salt):
        print("ERROR! This order has already occurred!")
        return False

    order_args = ["transfer", originator_address, taker_address, tokens, salt]

    if not verify_order(owner_address, owner_signature, owner_public_key, order_args):
        print("ERROR! The contract owner has not signed this order.")
        return False

    if not verify_order(originator_address, originator_signature, originator_public_key, order_args):
        print("ERROR! The address transferring tokens has not signed this!")
        return False

    if transfer_token(originator_address, taker_address, tokens):
        order_complete(salt)
        return True

    return False


def transfer_token_to(address_to, amount):
    """
    Transfer the specified amount of LOOT to an address within the smart contract..
    """
    context = GetContext()

    # The amount being transferred must be >= 1.
    if amount < 1:
        print("ERROR! Can only transfer an amount >= 1. ")
        return False

    # Add the LOOT to the address receiving the tokens and save it to storage.
    balance_to = balance_of(address_to)
    balance_to += amount
    Delete(context, address_to)
    Put(context, address_to, balance_to)

    return True


def transfer_token(address_from, address_to, amount):
    """
    Transfer the specified amount of LOOT from an address, to an address.
    """
    context = GetContext()

    # The amount being transferred must be > 0.
    if amount <= 0:
        return False

    # If the address is sending LOOT to itself, save on gas and return True.
    if address_from == address_to:
        return True

    # If the balance of the address sending the LOOT does not have enough, return False.
    balance_from = balance_of(address_from)
    if balance_from < amount:
        return False

    # Subtract the amount from the address sending the LOOT and save it to storage.
    balance_from -= amount
    Delete(context, address_from)
    Put(context, address_from, balance_from)

    # Add the LOOT to the address receiving the tokens and save it to storage.
    balance_to = balance_of(address_to)
    balance_to += amount
    Delete(context, address_to)
    Put(context, address_to, balance_to)

    return True


def handle_deposit(args):
    """
    Called when the NEP-5 LOOT contract calls this contract, we handle the deposited LOOT token.
    """
    address_from = args[0]
    address_to = args[1]
    amount = args[2]

    if len(address_from) != 20:
        return False

    if len(address_to) != 20:
        return False

    return increase_balance(address_from, amount)


def withdrawal_verified(my_hash, originator_address, tokens, originator_signature, originator_public_key,
                        owner_address, owner_signature, owner_public_key, salt):
    """
    Withdrawal on the framework must be verified.

    NOTE: Funds will always still be able to be withdrawn by a user back into the NEP-5 contract by other means.
    """

    if owner_address != contract_owner:
        print("ERROR! Owner address specified is not the contract owner.")
        return False

    if order_complete(salt):
        print("ERROR! This order has already occurred!")
        return False

    order_args = ["withdraw", originator_address, tokens, salt]

    if not verify_order(owner_address, owner_signature, owner_public_key, order_args):
        print("ERROR! The contract owner has not signed this order.")
        return False

    if not verify_order(originator_address, originator_signature, originator_public_key, order_args):
        print("ERROR! The address transferring tokens has not signed this!")
        return False

    return withdrawal(my_hash, originator_address, tokens)


def withdrawal(my_hash, originator_address, tokens):
    """ Withdraw from the smart contract, invoking the Loot NEP-5 contract. """

    balance = balance_of(originator_address)
    if tokens < 1 or tokens > balance:
        print("ERROR!: Unable to withdraw from contract!")
        return False

    params = [my_hash, originator_address, tokens]
    # if the transfer to the nep5 contract was successful, reduce the balance of their address in this contract
    if LootContract('transfer', params):
        reduce_balance(originator_address, tokens)
        return True

    return False


def balance_of(address):
    """
    Query the LOOT balance of an address.
    """
    context = GetContext()
    balance = Get(context, address)
    return balance


# endregion


def calculate_fees_of_order(marketplace, maker_address, taker_address, amount):
    """When an order has been filled between two parties, the owner of the
    marketplace can optionally take some fees.
    Maker gets charged once the order is filled.
    Taker get charged upon buying the order."""

    # Get the fees for this marketplace
    fee_address = get_fee_address(marketplace)
    maker_fee_rate = get_maker_fee(marketplace)
    taker_fee_rate = get_taker_fee(marketplace)

    # When a user buys -> they are charged a little extra
    # When a user sells -> they receive the price they put - some fees
    maker_fee = (amount * maker_fee_rate) / feeFactor
    taker_fee = (amount * taker_fee_rate) / feeFactor

    print("Maker fee: " + maker_fee)
    print("Taker fee: " + taker_fee)
    # Give funds to the marketplace owner.
    if not transfer_token(maker_address, fee_address, maker_fee):
        return False
    if not transfer_token(taker_address, fee_address, taker_fee):
        return False

    return True


def save_inventory(marketplace, address, inventory):
    """
    Helper method for inventory operations, saves a serialized list of items to storage.
    """
    context = GetContext()

    # Concatenate the specific storage key, delete the old storage
    # and add the updated inventory into storage.
    inventory_marketplace_key = concat(inventory_key, marketplace)
    storage_key = concat(inventory_marketplace_key, address)
    Delete(context, storage_key)
    Put(context, storage_key, inventory)

    return True


def get_inventory(marketplace, address):
    """
    Get the items the address owns on a marketplace.
    """
    context = GetContext()

    # Return the serialized inventory for the address.
    inventory_marketplace_key = concat(inventory_key, marketplace)
    storage_key = concat(inventory_marketplace_key, address)
    items_serialized = Get(context, storage_key)

    return items_serialized


# Marketplace Administration

def register_marketplace(marketplace, address, taker_fee, maker_fee):
    """
    Register a new marketplace on the blockchain.
    They can set their fees and the address the fees go to.
    """
    if not set_maker_fee(marketplace, maker_fee):
        return False
    if not set_taker_fee(marketplace, taker_fee):
        return False
    if not set_fee_address(marketplace, address):
        return False
    if not add_owner_wallet(marketplace, address):
        return False
    # Concatenate the owner key and save the address into storage.

    print("Successfully registered marketplace!")
    return True


def set_maker_fee(marketplace, fee):
    """
    Maker fees, fees for selling.
    """
    if fee > MAX_FEE:
        return False
    if fee < 0:
        return False
    context = GetContext()

    key = concat("makerFee", marketplace)
    Put(context, key, fee)

    return True


def set_taker_fee(marketplace, fee):
    """
    Taker fees, fees for buying.
    """
    if fee > MAX_FEE:
        return False
    if fee < 0:
        return False

    context = GetContext()
    key = concat("takerFee", marketplace)
    Put(context, key, fee)

    return True


def set_fee_address(marketplace, address):
    """
    Set who will receive the fees for this marketplace.
    """
    if len(address) != 20:
        return False
    context = GetContext()
    key = concat("feeAddress", marketplace)
    Put(context, key, address)

    return True


def get_fee_address(marketplace):
    """
    Get the taker fees set in a marketplace.
    """
    context = GetContext()
    key = concat("feeAddress", marketplace)
    fee_address = Get(context, key)
    return fee_address


def get_maker_fee(marketplace):
    """
    Get the maker fees set in a marketplace.
    """
    context = GetContext()
    key = concat("makerFee", marketplace)
    maker_fee = Get(context, key)
    return maker_fee


def get_taker_fee(marketplace):
    """
    Get the taker fees set in a marketplace.
    """
    context = GetContext()
    key = concat("takerFee", marketplace)
    taker_fee = Get(context, key)
    return taker_fee


def add_owner_wallet(marketplace, address):
    """
    Add an owner wallet, giving them exclusive rights to their marketplace.
    """
    context = GetContext()
    key_part1 = concat("key", address)
    owner_key = concat(marketplace, key_part1)
    owner = Get(context, owner_key)

    if owner == b'':
        Put(context, owner_key, address)
        return True

    return False


# Saving marketplace owners in seperate storage, costs less to search rather than a less.
def is_marketplace_owner(marketplace, address):
    """
    Check if the address is an owner of a marketplace.
    """
    context = GetContext()
    key_part1 = concat("key", address)
    owner_key = concat(marketplace, key_part1)
    owner = Get(context, owner_key)

    return owner != b''


# endregion


# region Decentralized GameModes & events.


def BR_create(event_code, marketplace, marketplace_owner_address, rewards):
    '''
    Create a new battle royale decentralized event, with the given rewards as prizes for the winners.
    :param event_code: The unique code of the event.
    :param marketplace: The game being hosted on.
    :param marketplace_owner_address: The address creating this event.
    :param rewards: A list of rewards given to the top players.
    :return: If created event successfully.
    '''

    # Currently only an owner can give out rewards for testing.
    if not is_marketplace_owner(marketplace, marketplace_owner_address):
        print("ERROR! Cannot start event: must be an owner of the marketplace.")
        return False

    if not CheckWitness(marketplace_owner_address):
        print("ERROR! Cannot start event: address is not a witness of the transaction.")
        return False

    context = GetContext()

    # Ensure an event with this code does not already exist.
    br_details_s = get_BR_event_details(context, event_code)

    if br_details_s != b'':
        print("ERROR! Cannot start event: event code is not unique.")
        return False

    # Create a new set of details for the event, and save this to storage to be queryable.
    # TODO lists suffice for building, but if necessary these lists can be more neatly done with dictionaries.
    br_details = [0, 0, marketplace_owner_address, False, 0, 0, 10, marketplace, 0]
    set_BR_event_details(context, event_code, br_details)

    # Add rewards at stake for the contest, may be any number n, s.t. n <= 12 (16 max parameters, 4 used).
    set_BR_rewards(context, event_code, rewards)

    return True


def BR_start(event_code, address):
    """
    Start the BR event.
    :param event_code: The unique code of the event.
    :param address: The address which is starting the event.
    :return: True if the event starts.
    """

    if not CheckWitness(address):
        print("ERROR: Cannot start event, no witness of this address attached to the transaction.")
        return False

    context = GetContext()

    br_details = get_BR_event_details(context, event_code)

    if br_details == b'':
        print("ERROR! Cannot start event, it does not exist.")
        return False

    br_details = Deserialize(br_details)

    if br_details[2] != address:
        print("ERROR! Cannot start event, is not the owner of the event.")
        return False

    player_list = get_BR_player_list(context, event_code)
    if player_list == b'':
        print("ERROR! No players, cannot start the match.")
        return False

    player_list = Deserialize(player_list)
    player_count = len(player_list)
    # Determine how large the x * y grid will be.
    # Starts at 3 x 3 currently for each player to keep a square shaped grid.
    player_count -= 1
    grid_length = 3 + player_count
    br_details[8] = grid_length  # Must store the grid length for calculations with boundaries and movement.
    grid_capacity = grid_length * grid_length
    # Take one as player can land at zones 0-15.
    grid_capacity -= 1
    br_details[1] = grid_capacity
    # Set the event to has begun.
    br_details[3] = True
    # Set the block in which the round has started, used an approximate time reference.
    br_details[4] = GetHeight()
    set_BR_event_details(context, event_code, br_details)

    return True


def BR_sign_up(event_code, address):
    """
    Currently anyone may sign up to the BR, it is a public decentralized contest.
    :param event_code: The unique code of the event.
    :param address: The address wanting to sign up.
    :return: If signed up successfully.
    """
    context = GetContext()

    # Get the stored details of the event.
    br_details = get_BR_event_details(context, event_code)

    if br_details == b'':
        print("ERROR! Cannot sign up to the event, there is no event running with this code.")
        return False

    br_details = Deserialize(br_details)

    if br_details[3]:
        print("ERROR! Event has begun can not sign up!")
        return False

    if not CheckWitness(address):
        print("ERROR! Cannot sign up to an event, witness is not attached to tx.")
        return False

    stored_entrant = get_BR_entrant_details(context, event_code, address)

    if stored_entrant != b'':
        print("ERROR! Cannot sign up to event, this address is already signed up.")
        return False

    # Add this player to a list of the active players and save into storage.
    list_of_players = get_BR_player_list(context, event_code)
    if list_of_players == b'':
        list_of_players = []
    else:
        list_of_players = Deserialize(list_of_players)
    list_of_players.append(address)
    set_BR_player_list(context, event_code, list_of_players)

    # Create a new entrant information list, and add it into storage so it may be queried.
    entrant_information = [0, 0, "", 0]
    set_BR_entrant_details(context, event_code, address, entrant_information)

    return True


def BR_choose_initial_grid_position(event_code, address, zone):
    """
    Every player is required to choose their initial position they will "land" in.
    :param event_code: The unique code of the event.
    :param address: The address performing the action.
    :param zone: The zone/grid position they want to be put in.
    :return: True if chooses initial zone/grid position.
    """
    context = GetContext()

    if not CheckWitness(address):
        print("ERROR! Cannot sign up to an event, witness is not attached to tx.")
        return False

    # Ensure the event exists.
    event_details = get_BR_event_details(context, event_code)

    if event_details == b'':
        print("ERROR! Cannot perform initial grid choice, event does not exist.")
        return False

    event_details = Deserialize(event_details)

    # Ensure the round is at 0.
    current_event_round = event_details[0]
    if current_event_round != 0:
        print("ERROR! Cannot perform spawn, round 0 has finished.")
        return False

    entrant_details = get_BR_entrant_details(context, event_code, address)

    if entrant_details == b'':
        print("ERROR! Cannot perform spawn, entrant does not exist in this event.")
        return False

    entrant_details = Deserialize(entrant_details)

    # Ensure the entrant is in round 0, e.g. they have not already landed.
    if entrant_details[1] > 0:
        print("ERROR! Cannot perform spawn, entrant current round is > 0.")
        return False

    # Ensure the player is not landing in a zone that is out of bounds.
    capacity = event_details[1]
    if zone > capacity or zone < 0:
        print("ERROR! Cannot perform spawn, landing zone is outside the bounds.")
        return False

    # Move and update the player to the next position, and place them into round 1.
    entrant_details[1] = 1
    # Move them to the zone.
    entrant_details[0] = zone
    set_BR_entrant_details(context, event_code, address, entrant_details)

    return True


def BR_do_action(event_code, address, action, direction):
    '''
    Perform an action, in the event, logic of the game is is all determined here.
    :param event_code: The unique code of the event.
    :param address: The address performing the action.
    :param action: The action being performed.
    :param direction: The direction the player wants to move.
    :return: True if the action was locked in, and the round resolved.
    '''

    context = GetContext()

    if not CheckWitness(address):
        print("ERROR: Cannot sign up to an event, witness is not attached to tx.")
        return False

    event_details = get_BR_event_details(context, event_code)

    if event_details == b'':
        print("ERROR: Cannot perform action, event does not exist.")
        return False

    event_details = Deserialize(event_details)

    entrant_details = get_BR_entrant_details(context, event_code, address)

    if entrant_details == b'':
        print("ERROR: Cannot perform action, entrant does not exist in this event.")
        return False

    entrant_details = Deserialize(entrant_details)

    if not event_details[3]:
        print("ERROR: Cannot resolve action, event has not begun.")
        return False

    # Must be > round 0, i.e. must spawn into the game first.
    if event_details[0] <= 0:
        print("ERROR: No action is available on round 0.")
        return False

    # The event current round must be lower or equal to the players recorded round.
    if event_details[0] < entrant_details[1]:
        print("ERROR: Player has already completed an action this round.")
        return False

    # Update player details which will be resolved next.
    entrant_details[1] = event_details[0] + 1
    entrant_details[2] = action
    entrant_details[3] = direction

    # Save details and resolve the round.
    set_BR_entrant_details(context, event_code, address, entrant_details)

    BR_resolve_round(event_code, address, event_details, entrant_details)

    return True


def BR_resolve_round(event_code, address, event_details, entrant_details):
    """
    Called internally by the smart contract to resolve a round after an address completes an action.
    :param event_code: The unique code of the event.
    :param address: The address performing the action.
    :param event_details: The stored details of the event.
    :param entrant_details: The stored details of the entrant.
    """

    context = GetContext()

    zone_caller_in = entrant_details[0]
    round_in = event_details[0]
    # This is why we have to store how many players we started the game so we can calculate boundaries.
    grid_side_length = event_details[8]
    caller_action = entrant_details[2]

    # Firstly, if the player is moving, perform that action.
    if caller_action == 'move':

        # Get the direction we are moving.
        direction_moving = entrant_details[3]

        print(direction_moving)

        # Traverse the grid in the direction we are moving.
        zone_to = zone_caller_in
        # UP
        if direction_moving == 0:
            zone_to += grid_side_length
        # DOWN
        elif direction_moving == 1:
            zone_to -= grid_side_length
        # RIGHT
        elif direction_moving == 2:
            zone_to += 1
        # LEFT
        elif direction_moving == 3:
            zone_to -= 1

        # If doing this move has not made us out of bounds, we can move the player.
        if not is_player_out_of_bounds(zone_to, grid_side_length, direction_moving, 0):
            # Move zone and save details.
            entrant_details[0] = zone_to
            set_BR_entrant_details(context, event_code, address, entrant_details)
            zone_caller_in = zone_to

    # Find the complete list of players who are not this address in the same zone.
    list_of_players_in_zone = []
    list_of_player_details_in_zone = []
    list_of_players = get_BR_player_list(context, event_code)
    list_of_players = Deserialize(list_of_players)

    for player in list_of_players:  # ~ 10
        if player != address:
            entrant = get_BR_entrant_details(context, event_code, player)
            if entrant != b'':
                entrant = Deserialize(entrant)
                # They must be in the same zone as the caller,
                # and they must of had a chance to perform a move for this round.
                if entrant[0] == zone_caller_in and entrant[1] == round_in + 1:
                    list_of_players_in_zone.append(player)
                    list_of_player_details_in_zone.append(entrant)

    # Resolve the combat for the round, if there is at least one other player in the grid.
    player_count_in_zone = len(list_of_players_in_zone)

    if player_count_in_zone > 0:
        # Get a random player in the zone to fight, and their details.
        player_index_vs = random_number_upper_limit(player_count_in_zone)

        address_vs = list_of_players_in_zone[player_index_vs]
        player_vs_details = list_of_player_details_in_zone[player_index_vs]
        opponent_action = player_vs_details[2]

        # Fight and publish the results.
        battle_result = BR_roll_combat(caller_action, opponent_action)

        payload = ["BR", event_code, "fight", round_in, address, address_vs, battle_result]
        Notify(payload)

        if battle_result:
            print("BATTLE! Win -> removing opponent from battle!")
            BR_remove_player(event_code, address_vs)

        else:
            print("BATTLE! Lost -> removing caller from battle!")
            # Remove and return true as complete.
            BR_remove_player(event_code, address)
            return False

    # If a player is looting and survived the round, we can loot items.
    if caller_action == "loot":
        BR_loot_action(event_code, round_in, address)

    return True


def BR_remove_player(event_code, address):
    '''
    Remove a player from the BR, after they lose determined by the sc.
    :param event_code:
    :param address:
    :return:
    '''
    # remove or mark as destroyed?
    context = GetContext()

    # Simply add the address to the leaderboard list,
    # and we display them in order of being knocked out, last player wins.
    leaderboard = get_BR_leaderboard(context, event_code)

    if leaderboard == b'':
        leaderboard = [address]
    else:
        leaderboard = Deserialize(leaderboard)
        leaderboard.append(address)

    set_BR_leaderboard(context, event_code, leaderboard)

    # Delete the entrant details so they can not perform any other action.
    half_key = concat(battle_royale_entrant_key, event_code)
    complete_key = concat(half_key, address)
    Delete(context, complete_key)

    # Finally remove the address from the list of active players.
    list_of_all_players = get_BR_player_list(context, event_code)
    list_of_all_players = Deserialize(list_of_all_players)

    current_index = 0

    for player in list_of_all_players:
        if player == address:
            list_of_all_players.remove(current_index)
            set_BR_player_list(context, event_code, list_of_all_players)
            return list_of_all_players
        current_index += 1

    return list_of_all_players


def BR_loot_action(event_code, current_round, address):
    """
    Called internally by the smart contract when a user performs a loot action.
    These events are caught and if the user found an item they are given in the game.
    :param event_code: The unique code of the event.
    :param current_round: The current round to calculate the drop chance.
    :param address: The address performing the loot action.
    :return: True
    """

    # Calculate the current chance to find loot and roll it.
    chance_to_find_loot = BR_CHANCE_TO_FIND_LOOT + (BR_CHANCE_INCREASE_PER_ROUND * current_round)

    rolled_item = random_number_0_100() <= chance_to_find_loot
    rolled_reward = -1

    if rolled_item:
        upper_limit = len(BR_UNTRADEABLE_REWARDS) - 1
        rolled_reward = random_number_upper_limit(upper_limit)

    # Notify if an item was rolled.
    payload = ["BR", event_code, "loot", address, rolled_reward]
    Notify(payload)

    return True


def BR_roll_combat(caller_action, opponent_action):
    """
    Internally called by the smart contract to fairly decide the outcome of combat between players.
    :param caller_action: The action being performed by the caller.
    :param opponent_action: The action being performed by the opponent.
    :return: True if the caller wins.
    """

    if caller_action == "loot" or caller_action == "move":
        # If the caller is looting or moving they are at a disadvantage.
        if opponent_action == "hide":
            caller_win_chance = 40
        else:
            caller_win_chance = 50

    elif caller_action == "hide":
        # If the opponent is hiding they are at the advantage.
        if opponent_action == "hide":
            caller_win_chance = 50
        # If the caller is hiding and opponent is not hiding, caller has 60% chance to win
        else:
            caller_win_chance = 60
    else:
        # if unknown command, the caller loses, as they did not select a valid action.
        return False

    return random_number_0_100() <= caller_win_chance


def BR_finish_round(event_code):
    """
    Called by anyone to finish an event, will only finish if the conditions are met.
    # Best case, ~30s each round.
    # Worst case, ~3min each round.
    :param event_code: The unique code of the event.
    :return: True if the event was finished.
    """

    context = GetContext()
    height = GetHeight()

    br_details = get_BR_event_details(context, event_code)

    if br_details == b'':
        print("ERROR! Cannot end round, event does not exist.")
        return False

    br_details = Deserialize(br_details)

    # If the battle has not started, return false.
    if not br_details[3]:
        print("ERROR! Cannot end round, battle royale event has not begun!")
        return False

    round_start_height = br_details[4]

    # If 10 blocks have past, the round has timed out.
    if height - round_start_height >= BR_ROUND_TIMEOUT:
        return BR_on_round_finish(event_code, br_details, context, height)
    # If we have not timed out we check if every player has completed an action for this round so we can finish early.
    else:
        list_of_players = get_BR_player_list(context, event_code)
        list_of_players = Deserialize(list_of_players)

        for player in list_of_players:
            entrant = get_BR_entrant_details(context, event_code, player)
            if entrant != b'':
                entrant = Deserialize(entrant)
                if entrant[1] <= br_details[0]:
                    print("ERROR! A player has not made a move for this round.")
                    payload = ['BR', event_code, 'round_end', br_details[0], False]
                    Notify(payload)
                    return False

        # All players are done!
        return BR_on_round_finish(event_code, br_details, context, height)


def BR_on_round_finish(event_code, br_details, context, height):
    """
    Called internally by the smart contract to conclude a round.
    :param event_code: The unique code of the event.
    :param br_details: The details of the BR event.
    :param context: The storage context.
    :param height: The current height of the blockchain.
    :return: True if the round was resolved.
    """

    # Set the height and increment the round.
    br_details[4] = height
    br_details[0] = br_details[0] + 1

    # Update BR details to next round.
    set_BR_event_details(context, event_code, br_details)

    # Get the list of active players.
    list_of_players = get_BR_player_list(context, event_code)
    list_of_players = Deserialize(list_of_players)

    # Check if zone needs to be destroyed now,
    # we can bundle that up with checking if they have moved to save gas.
    if br_details[0] >= ROUND_DESTROYED_ZONES_GENERATE:
        # Returns a list of players that survived through the destroyed zones.
        list_of_players = BR_destroy_next_zone(event_code, br_details[0], br_details[8])
    # If we have not checked players that have not moved yet, do so.
    else:
        # Remove players that did not perform an action this turn.
        # This has to occur is seperate steps or will not work as we cannot mutate a list during iteration.
        removed_players_address = []

        for player in list_of_players:
            entrant = get_BR_entrant_details(context, event_code, player)
            if entrant != b'':
                entrant = Deserialize(entrant)
                if entrant[1] != br_details[0]:
                    removed_players_address.append(player)

        for i in range(0, len(removed_players_address)):
            # Now we can remove players without mutating the original list during iteration.
            list_of_players = BR_remove_player(event_code, removed_players_address[i])

            payload = ["BR", event_code, "removed_player", removed_players_address[i]]
            Notify(payload)

    remaining_player_count = len(list_of_players)

    print("----- Remaining player count -----")
    print(remaining_player_count)
    print("----------------------------------")
    # If there are <= one player, we should end the event.
    if remaining_player_count <= 1:
        # If there is a final playing remaining, remove him and end the match.
        if remaining_player_count > 0:
            last_player_address = list_of_players[0]
            BR_remove_player(event_code, last_player_address)

        return BR_end_event(event_code, br_details, context)

    payload = ['BR', event_code, 'round_end', br_details[0], True]
    Notify(payload)

    return True


def BR_end_event(event_code, event_details, context):
    """
    Called from within the contract when the event ends.
    Pays out items to the top x players dependent on the length
    of rewards the event was initialized with.
    :param event_code: The unique event code of the event.
    :param event_details: The details of the event.
    :param context: The storage context.
    :return: True if the event ended.
    """

    # Remove the event as it is complete to clean up storage.
    # The leaderboard remains.
    remove_BR_event_details(context, event_code)

    leaderboard = get_BR_leaderboard(context, event_code)
    leaderboard = Deserialize(leaderboard)

    # Get the rewards of the event.
    rewards = get_BR_rewards(context, event_code)

    if rewards == b'':
        print("ERROR: No rewards exist for this event.")
        return True

    rewards = Deserialize(rewards)

    for i in range(0, len(rewards)):
        # As we are giving it to the last added addresses to the list, those whom survived the longest.
        if len(leaderboard) > 0 and i <= len(leaderboard) - 1:
            # Winners are the last x players s.t. x == len(rewards) for now.
            index = len(leaderboard) - 1
            # Get the last player - i in the list.
            index = index - i
            address = leaderboard[index]
            reward = rewards[i]
            marketplace = event_details[7]

            give_item(marketplace, address, reward)

            # Acknowledge that a user received a reward.
            payload = ["BR", event_code, "received_reward", address, reward]
            Notify(payload)

    # Can then query the leaderboard to see winners outside.
    payload = ["BR", event_code, "event_complete", True]
    Notify(payload)

    return True


def BR_destroy_next_zone(event_code, round_on, grid_length):
    """
    This is only called after advancing a zone.
    Mark a zone for destruction, and destroy a previous
    zone if there is one.
    This encourages the player to move from their zone.
    This way, the next side that will be stripped from the map will always be random .
    :param event_code: The unique code of the event.
    :param round_on: The current round the event is on.
    :param grid_length: The length of a side of the grid map.
    :return: List of players which were not in a destroyed zone.
    """

    context = GetContext()

    print("-----Destroying next marked zone.-----")

    # Check if there is a previous marked zone.
    # Marked zone will be a marked side, so the side the gas is coming in on.
    current_destroyed_depths = get_BR_destroyed_zone_depths(context, event_code)

    # Grab the list of remaining players.
    player_list = get_BR_player_list(context, event_code)
    player_list = Deserialize(player_list)

    # If the depths have been initialized.
    if current_destroyed_depths != b'':
        current_destroyed_depths = Deserialize(current_destroyed_depths)

        removed_address_list = []

        # The grid has 4 sides that can be marked off, iterate through these.
        for i in range(0, 4):
            # If the current depth is > 0, meaning the side has been destroyed.
            current_depth = current_destroyed_depths[i]
            if current_depth > 0:
                # If there is a depth change here, we can check once per side if the player is out of range.
                # We are now checking to see if the player is out of bounds.
                for player in player_list:  # ~10
                    entrant = get_BR_entrant_details(context, event_code, player)
                    if entrant != b'':
                        entrant = Deserialize(entrant)
                        zone_entrant_is_in = entrant[0]
                        # Out of bounds ? if so remove them.
                        entrant_out_of_bounds = is_player_out_of_bounds(zone_entrant_is_in, grid_length, i,
                                                                        current_destroyed_depths[i])
                        # Did they perform an action this round before it timed out ? if not, remove them.
                        entrant_did_not_do_action = entrant[1] != round_on
                        if entrant_out_of_bounds or entrant_did_not_do_action:
                            removed_address_list.append(player)

        # Remove the list of players for the remaining players list and notify each removal.
        for i in range(0, len(removed_address_list)):
            player_list = BR_remove_player(event_code, removed_address_list[i])

            payload = ["BR", event_code, "removed_player", removed_address_list[i]]
            Notify(payload)

    else:
        # Initialize the list of depths the "poison" has consumed the sides,
        # and has in turn stripped down the grid map area.
        current_destroyed_depths = [0, 0, 0, 0]

    # Pick a new random side for the gas to come from next round, and notify the event.
    # So we can increment to say the depth of that row has increased, that will be checked next round to give players
    # a chance to move.
    side_gas_is_coming = random_number_upper_limit(4)
    value = current_destroyed_depths[side_gas_is_coming]
    current_destroyed_depths[side_gas_is_coming] = value + 1
    set_BR_destroyed_zone_depths(context, event_code, current_destroyed_depths)

    # Notify players that a zone has been marked so they have a chance to move.
    payload = ["BR", event_code, "zone_marked", side_gas_is_coming]
    Notify(payload)

    return player_list


def is_player_out_of_bounds(zone_on, grid_length, side, depth):
    """
    Check if a player is outside the bounds of the map.
    :param zone_on: The zone the player is currently on.
    :param grid_length: The length of the grid, determined at the beginning of the match.
    :param side: The side we are checking if out of bounds. As a player can only move one square at a time.
    :param depth: The depth of the side that is "eliminated", essentially how many times the "poison" has occurred.
                The players row/column must be within this depth.
                Can check if the player is out of bounds of the normal map with depth = 0.
    :return: True if out of bounds.
    """
    # We can calculate the boundaries of the grid and check if the player is out of bounds.

    # TOP
    if side == 0:
        row_in = zone_on / grid_length

        row_in = (grid_length - row_in) - 1

        if row_in <= depth - 1:
            return True
    # BOTTOM
    elif side == 1:
        row_in = zone_on / grid_length
        # e.g. if we are row 0, and depth is 1, we are out
        # if we are row 1 and depth is 1 we are fine
        if row_in <= depth - 1:
            return True
    # EAST
    elif side == 2:

        t = grid_length - 1
        b = zone_on % grid_length
        column_in = t - b
        # If the column we are in is
        if column_in <= depth - 1:
            return True
    # WEST
    elif side == 3:
        column_in = zone_on % grid_length

        if column_in <= depth - 1:
            return True

    return False


# BR Mutators

def set_BR_event_details(context, event_code, details):
    ''' Details of the BR event, capacity, owner, etc.'''
    key = concat(battle_royale_details_key, event_code)
    br_details_s = Get(context, key)
    if br_details_s != b'':
        Delete(context, key)
    br_details_s = Serialize(details)
    Put(context, key, br_details_s)
    return True


def set_BR_entrant_details(context, event_code, address, details):
    ''' Details of the entrant, round action, action, etc.'''
    half_key = concat(battle_royale_entrant_key, event_code)
    complete_key = concat(half_key, address)
    stored_entrant_s = Get(context, complete_key)
    if stored_entrant_s != b'':
        Delete(context, complete_key)
    details_s = Serialize(details)
    Put(context, complete_key, details_s)
    return True


def set_BR_destroyed_zone_depths(context, event_code, zones):
    ''' A list of zones that any player on them will be disqualified. '''
    br_destroyed_zones_key = concat(battle_royale_destroyed_zones_key, event_code)
    destroyed_zones_s = Get(context, br_destroyed_zones_key)
    if destroyed_zones_s != b'':
        Delete(context, br_destroyed_zones_key)
    zones_s = Serialize(zones)
    Put(context, br_destroyed_zones_key, zones_s)
    return True


def set_BR_rewards(context, event_code, rewards):
    ''' A list of the rewards of a BR event.'''
    rewards_s = Serialize(rewards)
    key = concat(battle_royale_rewards_key, event_code)
    Put(context, key, rewards_s)
    return True


def set_BR_marked_zone(context, event_code, zone):
    key = concat(battle_royale_marked_destroyed_zone_key, event_code)
    Put(context, key, zone)
    return True


def set_BR_leaderboard(context, event_code, leaders):
    key = concat(battle_royale_event_results_key, event_code)
    leaderboard_s = Get(context, key)
    if leaderboard_s != b'':
        Delete(context, key)
    leaders_s = Serialize(leaders)
    Put(context, key, leaders_s)
    return True


def set_BR_player_list(context, event_code, players):
    key = concat(battle_royale_current_players_key, event_code)
    players_s = Get(context, key)
    if players_s != b'':
        Delete(context, key)
    players_s = Serialize(players)
    Put(context, key, players_s)
    return True


# BR Accessors

"""
Note: When getting from storage we must send these values in the serialized form,
      and deserialize at the initial method call.
"""


def get_BR_event_details(context, event_code):
    ''' Details of the BR event, capacity, owner, etc.'''
    key = concat(battle_royale_details_key, event_code)
    br_details = Get(context, key)
    return br_details


def get_BR_entrant_details(context, event_code, address):
    ''' Details of the entrant, round action, action, etc.'''
    half_key = concat(battle_royale_entrant_key, event_code)
    complete_key = concat(half_key, address)
    stored_entrant = Get(context, complete_key)
    # stored_entrant = Deserialize(stored_entrant_s)
    return stored_entrant


def get_BR_destroyed_zone_depths(context, event_code):
    ''' A list of zones that any player on them will be disqualified. '''
    br_destroyed_zones_key = concat(battle_royale_destroyed_zones_key, event_code)
    destroyed_zones = Get(context, br_destroyed_zones_key)
    # destroyed_zones = [] if destroyed_zones_s == b'' else Deserialize(destroyed_zones_s)
    return destroyed_zones


def get_BR_rewards(context, event_code):
    ''' A list of the rewards of a BR event.'''
    key = concat(battle_royale_rewards_key, event_code)
    rewards = Get(context, key)
    # rewards = [] if rewards_s == b'' else Deserialize(rewards_s)
    return rewards


def get_BR_marked_zones(context, event_code):
    key = concat(battle_royale_marked_destroyed_zone_key, event_code)
    zone = Get(context, key)
    return zone


def get_BR_player_list(context, event_code):
    key = concat(battle_royale_current_players_key, event_code)
    players = Get(context, key)
    return players


def get_BR_leaderboard(context, event_code):
    key = concat(battle_royale_event_results_key, event_code)
    leaderboard = Get(context, key)
    # leaderboard = [] if leaderboard_s == b'' else Deserialize(leaderboard_s)
    return leaderboard


def remove_BR_event_details(context, event_code):
    key = concat(battle_royale_details_key, event_code)
    br_details_s = Get(context, key)
    if br_details_s != b'':
        Delete(context, key)
    return True


# Random number generation

def random_number_0_100():
    height = GetHeight()
    header = GetHeader(height)
    index = header.ConsensusData
    random_number = index % 99
    return random_number


def random_number_upper_limit(limit):
    height = GetHeight()
    header = GetHeader(height)
    random_number = header.ConsensusData >> 32
    result = (random_number * limit) >> 32

    return result

# endregion
