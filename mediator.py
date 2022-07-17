'''
The below contract, 'Mediator' does the following:
- Consider two parties, alice and bob.
- Say Alice wants to sell some physical product x (some artwork etc) to Bob.
- Also assume Alice wants the transaction to happen in more secure manner.
- The normal centralized way would be to post the product details to an e-commerce mediater portal, where multiple other parties post their products. 
  Bob will come to the portal and search for his required product (say it is the same x product). Then he makes the payment to the portal.
  Then the portal transfers the amount (with some commision deducted) to Alice and then the portal sends the product x to Bob.
- The above centralized flow has the following limitations:
    - All the parties should trust the portal.
    - Parties need to pay some un-necessary commision fees to the mediater portal.
- Hence the following solution solves both the problems:
    - The below smart contract acts as the mediater portal that is discussed above.
- Though, the usual decentralized flow has the following limitations:
    - In case of centralized portal, the product x is handed over to the trustable mediater portal.
      But thats not the case here.
- So we have the following to deal in case of decentralized solution of the above tradeoff:
    - Bob pays the amount, but Alice doesn't deliver the product, without involvement of any physical mediater.
- The following algorithm (which is also implemented below) provides a solution:
    - Alice sets the price (say p) of item in the smart contract and deposits twice that price into the same contract. ('sell' entry point does that)
    - Then Bob comes in and if he wants to get this same product, then even he deposits the same amount in the same contract to buy it. ('buy' entry point does that)
    - So at the end of above two steps, the contract will have 4p.
    - Now there are two possibilities:
        - If Bob actually receives the item physically, then he confirms using 'received' entry point. Then we are doing the following:
            - Send back p amount to Bob.
            - Send 3p amount to Alice.
        - If Alice want to unsell the item itself completely, then she confirms the same using 'unsell' entry point. The we are doing the following:
            - Send back 2p amount to Alice
            - Send back 2p amount to Bob.
        NOTE: If Alice want to cheat Bob by not delivering the item, it cannot happen, as Alice is getting a loss of 2p in the process of getting p profit by not delivering the item.
'''

import smartpy as sp

'''
DEFAULTS class stores the default Alice address and default Bob address
'''
class DEFAULTS: 
    def default_seller():
        return sp.address("tz1YtuZ4vhzzn7ssCt93Put8U9UJDdvCXci4")

    def default_buyer():
        return sp.address("tz1YtuZ4vhzzn7ssCt93Put8U9UJDdvCXci4")

'''
Mediator contract contains implemnentations of the following functions (entry points):
- sell
- buy
- received
- unsell
- reset_contract
'''
class Mediator(sp.Contract):
    def __init__(self):
        self.init(
            product = sp.record(item_id = sp.nat(0), price = sp.nat(0)), # Stores the product details
            seller = DEFAULTS.default_seller(), # Stores the seller address
            buyer = DEFAULTS.default_buyer(), # Stores the buyer address
            seller_is_set = False, # Keeps a check if seller is set or not
            buyer_is_set = False # Keeps a check if buyer is set or not
        )
    
    '''
    Seller will call this to put any product up for sale
    '''
    @sp.entry_point
    def sell(self, params):
        # Set params type
        sp.set_type(params.item_id, sp.TNat)
        sp.set_type(params.price, sp.TNat)

        # Verify that seller is not yet set and also verify that the stake is as required
        sp.verify(~self.data.seller_is_set, message = "Contract already in use.")
        sp.verify(sp.amount == sp.utils.nat_to_mutez(2 * params.price), message = "Stake should be two times the product price.")

        # Set the seller and the product
        self.data.product.item_id = params.item_id
        self.data.product.price = params.price
        self.data.seller = sp.sender
        self.data.seller_is_set = True

    '''
    Buyer will call this by providing the item id he wants to buy
    '''
    @sp.entry_point
    def buy(self, params):
        # Set params type
        sp.set_type(params.item_id, sp.TNat)
        
        # Verify that seller is set but buyer is not yet set and also verify that the stake is as required
        sp.verify(self.data.seller_is_set, message = "Product not yet set.")
        sp.verify(~self.data.buyer_is_set, message = "Contract already in use.")
        sp.verify(sp.amount == sp.utils.nat_to_mutez(2 * self.data.product.price), message = "Stake should be two times the product price.")

        # Set the buyer
        self.data.buyer = sp.sender
        self.data.buyer_is_set = True
    
    '''
    Buyer will call this to confirm the delivery of the product
    '''
    @sp.entry_point
    def received(self, params):
        # Set params type
        sp.set_type(params.item_id, sp.TNat)

        # Verify that seller is set, buyer is set and the person calling the entry point is the buyer himself
        sp.verify(self.data.seller_is_set, message = "Seller not yet set.")
        sp.verify(self.data.buyer_is_set, message = "Buyer not yet set.")
        sp.verify(sp.sender == self.data.buyer, message = "You are not the buyer.")

        # Distribute the amount accordingly
        sp.send(sp.sender, sp.utils.nat_to_mutez(self.data.product.price))
        sp.send(self.data.seller, sp.utils.nat_to_mutez(3 * self.data.product.price))

        # Reset the contract as the trasaction between two parties is now completed
        self.reset_contract()

    '''
    Seller will call this if he no more wants to sell his product
    '''
    @sp.entry_point
    def unsell(self, params):
        # Set params type
        sp.set_type(params.item_id, sp.TNat)
        
        # Verify that seller is set, buyer is set and the person calling the entry point is the seller himself
        sp.verify(self.data.seller_is_set, message = "Seller not yet set.")
        sp.verify(self.data.buyer_is_set, message = "Buyer not yet set.")
        sp.verify(sp.sender == self.data.seller, message = "You are not the seller.")

        # Distribute the amount accordingly
        sp.send(sp.sender, sp.utils.nat_to_mutez(2 * self.data.product.price))
        sp.send(self.data.buyer, sp.utils.nat_to_mutez(2 * self.data.product.price))

        # Reset the contract as the trasaction between two parties is now cancelled
        self.reset_contract()
    
    '''
    This is a helper function to reset the contract (reset buyer, seller and the product)
    '''
    def reset_contract(self):
        self.data.product = sp.record(item_id = sp.nat(0), price = sp.nat(0))
        self.data.buyer_is_set = False
        self.data.seller_is_set = False

'''
Tests for the Mediator contract
'''
@sp.add_test(name = "Mediator Contract Tests")
def test():

    scenario = sp.test_scenario()
    scenario.h1("Mediator Contract")
    scenario.table_of_contents()

    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    scenario.h2("Accounts")
    scenario.show([alice, bob])

    scenario.h2("Methods")
    contract = Mediator()
    scenario += contract

    scenario.p("Alice is selling product x.")
    params = sp.record(item_id = 1, price = 1000000)
    contract.sell(params).run(sender = alice, amount = sp.tez(2))

    scenario.p("Bob is willing to buy product x.")
    params = sp.record(item_id = 1)
    contract.buy(params).run(sender = bob, amount = sp.tez(2))

    scenario.p("(a) Bob confirms the product x delivery.")
    params = sp.record(item_id = 1)
    contract.received(params).run(sender = bob)

    scenario.p("(b) Alice unsells the product x.")
    params = sp.record(item_id = 1)
    contract.unsell(params).run(sender = alice, valid = False)
