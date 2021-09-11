from pyteal import *

def approval_program():
    on_creation = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        App.globalPut(Bytes("startDate"), Btoi(Txn.application_args[0])),
        App.globalPut(Bytes("endDate"), Btoi(Txn.application_args[1])),
        App.globalPut(Bytes("nftId"), Btoi(Txn.application_args[2])),
        App.globalPut(Bytes("nftOwner"), Txn.sender()),
        App.globalPut(Bytes("bestOffer"), Int(0)),
        App.globalPut(Bytes("bestBidder"), Int(0)),
        App.globalPut(Bytes("statelessAddress"), Global.zero_address()),
        App.globalPut(Bytes("isOpen"), Int(0)),
        App.globalPut(Bytes("isNFTClaimed"), Int(0)),
        App.globalPut(Bytes("isMoneyClaimed"), Int(0)),
        App.globalPut(Bytes("totalOffer"), Int(0)),
        Return(Int(1))
    ])

    is_owner = App.globalGet(Bytes("nftOwner")) == Txn.sender()

    best_bidder_closeout = Seq([
        Assert(App.globalGet(Bytes("isNFTClaimed")) == Int(1)),
        Return(Int(1))
    ])

    bidder_closeout = Seq([
        Assert(App.localGet(Int(0), Bytes("totalOffer")) <= Int(0)),
        Return(Int(1))
    ])

    nft_owner_closeout = Seq([
        Assert(App.globalGet(Bytes("isMoneyClaimed")) == Int(1)),
        Return(Int(1))
    ])

    on_closeout = Cond(
        [Txn.sender() == App.globalGet(Bytes("bestBidder")), best_bidder_closeout],
        [And(Txn.sender() != App.globalGet(Bytes("bestBidder")),
             Txn.sender() != App.globalGet(Bytes("nftOwner"))),
        bidder_closeout],
        [Txn.sender() == App.globalGet(Bytes("nftOwner")), nft_owner_closeout]
    )

    on_delete_open = Seq([
        Assert(is_owner),
        Assert(App.globalGet(Bytes("isMoneyClaimed")) == Int(1)),
        Assert(App.globalGet(Bytes("isNFTClaimed")) == Int(1)),
        Assert(App.globalGet(Bytes("totalOffer")) <= Int(0)),
        Return(Int(1))
    ])

    on_delete = Cond(
        [App.globalGet(Bytes("isOpen")) == Int(1), on_delete_open],
        [App.globalGet(Bytes("isOpen")) == Int(0), Return(is_owner)],
    )

    on_optin = Seq([
        App.localPut(Int(0), Bytes("totalOffer"), Int(0)),
        Return(Int(1))
    ])

    open_auction = Seq([
        Assert(Txn.application_args.length() >= Int(2)),
        Assert(is_owner),
        App.globalPut(Bytes("statelessAddress"), Txn.application_args[1]),
        Return(Int(1))
    ])

    deposit_nft = Seq([
        Assert(Global.group_size() >= Int(2)),
        Assert(is_owner),
        Assert(Gtxn[Global.group_size() - Int(1)].sender() == App.globalGet(Bytes("nftOwner"))),
        Assert(Gtxn[Global.group_size() - Int(1)].xfer_asset() == App.globalGet(Bytes("nftId"))),
        Assert(Gtxn[Global.group_size() - Int(1)].asset_amount() >= Int(1)),
        Assert(Gtxn[Global.group_size() - Int(1)].asset_receiver() == App.globalGet(Bytes("statelessAddress"))),
        App.globalPut(Bytes("isOpen"), Int(1)),
        Return(Int(1))
    ]);

    bid = Seq([
        Assert(Global.group_size() >= Int(2)),
        Assert(App.globalGet(Bytes("isOpen"))),
        Assert(Gtxn[Global.group_size() - Int(1)].receiver() == App.globalGet(Bytes("statelessAddress"))),
        Assert(Gtxn[Global.group_size() - Int(1)].amount() > App.globalGet(Bytes("bestOffer"))),
        App.globalPut(Bytes("bestOffer"), Gtxn[Global.group_size() - Int(1)].amount()),
        App.globalPut(Bytes("bestBidder"), Gtxn[Global.group_size() - Int(1)].sender()),
        App.globalPut(Bytes("totalOffer"),
            Gtxn[Global.group_size() - Int(1)].amount() + App.globalGet(Bytes("totalOffer"))),
        App.localPut(Int(0), Bytes("totalOffer"),
            Gtxn[Global.group_size() - Int(1)].amount() + App.localGet(Int(0), Bytes("totalOffer"))),
        Return(Int(1))
    ])



    # ##########################################################################
    claim_nft = Seq([
        # check general status
        Assert(App.globalGet(Bytes("isOpen"))),
        Assert(App.globalGet(Bytes("isNFTClaimed")) == Int(0)),
        Assert(Txn.sender() == App.globalGet(Bytes("bestBidder"))),
        Assert(Global.latest_timestamp() > App.globalGet(Bytes("endDate"))),

        # Check the previous transaction in the atomic transaction to ensure
        # the right NFT is being sent to the right address
        Assert(Global.group_size() >= Int(2)),
        Assert(Gtxn[Global.group_size() - Int(1)].receiver() == Txn.sender()),
        Assert(Gtxn[Global.group_size() - Int(1)].sender() == App.globalGet(Bytes("statelessAddress"))),
        Assert(Gtxn[Global.group_size() - Int(1)].xfer_asset() == App.globalGet(Bytes("nftId"))),
        Assert(Gtxn[Global.group_size() - Int(1)].asset_amount() == Int(1)),

        # Update global state and return
        App.globalPut(Bytes("isNFTClaimed"), Int(1)),
        Return(Int(1))
    ])


    # ##########################################################################
    claim_best_bid = Seq([
        # check general status
        Assert(App.globalGet(Bytes("isOpen"))),
        Assert(Txn.sender() == App.globalGet(Bytes("nftOwner"))),
        Assert(Global.latest_timestamp() > App.globalGet(Bytes("endDate"))),

        # Check the previous transaction in the atomic transaction to ensure
        # the right amount is being sent to the right address
        Assert(Global.group_size() >= Int(2)),
        Assert(Gtxn[Global.group_size() - Int(1)].receiver() == Txn.sender()),
        Assert(Gtxn[Global.group_size() - Int(1)].sender() == App.globalGet(Bytes("statelessAddress"))),
        Assert(Gtxn[Global.group_size() - Int(1)].amount() == App.globalGet(Bytes("bestOffer"))),

        # Update global state and return
        App.globalPut(Bytes("isMoneyClaimed"), Int(1)),
        App.globalPut(Bytes("totalOffer"),
                      App.globalGet(Bytes("totalOffer")) - App.globalGet(Bytes("bestOffer"))),
        Return(Int(1))
    ])


    # ##########################################################################
    claim_money_for_normal = Seq([
        # check general status
        Assert(App.globalGet(Bytes("isOpen"))),
        Assert(Global.latest_timestamp() > App.globalGet(Bytes("endDate"))),
        Assert(App.localGet(Int(0), Bytes("totalOffer")) > Int(0)),

        # Check the previous transaction in the atomic transaction to ensure
        # the right amount is being sent to the right address
        Assert(Global.group_size() >= Int(2)),
        Assert(Gtxn[Global.group_size() - Int(1)].receiver() == Txn.sender()),
        Assert(Gtxn[Global.group_size() - Int(1)].sender() == App.globalGet(Bytes("statelessAddress"))),
        Assert(Gtxn[Global.group_size() - Int(1)].amount() == App.localGet(Int(0), Bytes("totalOffer"))),

        # Update state and return
        App.globalPut(Bytes("totalOffer"),
                      App.globalGet(Bytes("totalOffer")) - App.localGet(Int(0), Bytes("totalOffer"))),
        App.localPut(Int(0), Bytes("totalOffer"), Int(0)),
        Return(Int(1))
    ])

    claim_money_for_best_bidder = Seq([
        # check general status
        Assert(App.globalGet(Bytes("isOpen"))),
        Assert(Global.latest_timestamp() > App.globalGet(Bytes("endDate"))),
        Assert(App.localGet(Int(0), Bytes("totalOffer")) > Int(0)),

        # Check for zero amount transaction to prevent spamming
        # and the host to pay for transaction fee over and over.
        Assert(Gtxn[Global.group_size() - Int(1)].amount() != Int(0)),

        # Check the previous transaction in the atomic transaction to ensure
        # the right amount is being sent to the right address
        Assert(Global.group_size() >= Int(2)),
        Assert(Gtxn[Global.group_size() - Int(1)].receiver() == Txn.sender()),
        Assert(Gtxn[Global.group_size() - Int(1)].sender() == App.globalGet(Bytes("statelessAddress"))),
        Assert(
            Gtxn[Global.group_size() - Int(1)].amount()
            == (App.localGet(Int(0), Bytes("totalOffer")) - App.globalGet(Bytes("bestOffer")))
        ),

        # Update state and return
        App.globalPut(Bytes("totalOffer"),
                      App.globalGet(Bytes("totalOffer"))
                      - App.localGet(Int(0), Bytes("totalOffer"))
                      + App.globalGet(Bytes("bestOffer"))),
        App.localPut(Int(0),
                     Bytes("totalOffer"),
                     App.localGet(Int(0), Bytes("totalOffer")) - App.globalGet(Bytes("bestOffer"))),
        Return(Int(1))
    ])

    claim_lost_bid_money = Cond(
        [Txn.sender() == App.globalGet(Bytes("bestBidder")), claim_money_for_best_bidder],
        [Txn.sender() != App.globalGet(Bytes("bestBidder")), claim_money_for_normal]
    )



    # register = Seq([
    #     App.localPut(Int(0), Bytes("balance"), Int(0)),
    #     Return(Int(1))
    # ])

    # # configure the admin status of the account Txn.accounts[1]
    # # sender must be admin
    # new_admin_status = Btoi(Txn.application_args[1])
    # set_admin = Seq([
    #     Assert(And(is_admin, Txn.application_args.length() == Int(2))),
    #     App.localPut(Int(1), Bytes("admin"), new_admin_status),
    #     Return(Int(1))
    # ])
    # # NOTE: The above set_admin code is carefully constructed. If instead we used the following code:
    # # Seq([
    # #     Assert(Txn.application_args.length() == Int(2)),
    # #     App.localPut(Int(1), Bytes("admin"), new_admin_status),
    # #     Return(is_admin)
    # # ])
    # # It would be vulnerable to the following attack: a sender passes in their own address as
    # # Txn.accounts[1], so then the line App.localPut(Int(1), Bytes("admin"), new_admin_status)
    # # changes the sender's admin status, meaning the final Return(is_admin) can return anything the
    # # sender wants. This allows anyone to become an admin!

    # # move assets from the reserve to Txn.accounts[1]
    # # sender must be admin
    # mint_amount = Btoi(Txn.application_args[1])
    # mint = Seq([
    #     Assert(Txn.application_args.length() == Int(2)),
    #     Assert(mint_amount <= App.globalGet(Bytes("reserve"))),
    #     App.globalPut(Bytes("reserve"), App.globalGet(Bytes("reserve")) - mint_amount),
    #     App.localPut(Int(1), Bytes("balance"), App.localGet(Int(1), Bytes("balance")) + mint_amount),
    #     Return(is_admin)
    # ])

    # # transfer assets from the sender to Txn.accounts[1]
    # transfer_amount = Btoi(Txn.application_args[1])
    # transfer = Seq([
    #     Assert(Txn.application_args.length() == Int(2)),
    #     Assert(transfer_amount <= App.localGet(Int(0), Bytes("balance"))),
    #     App.localPut(Int(0), Bytes("balance"), App.localGet(Int(0), Bytes("balance")) - transfer_amount),
    #     App.localPut(Int(1), Bytes("balance"), App.localGet(Int(1), Bytes("balance")) + transfer_amount),
    #     Return(Int(1))
    # ])

    result = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.OptIn, on_optin],
        [Txn.application_args[0] == Bytes("openAuction"), open_auction],
        [Txn.application_args[0] == Bytes("depositNFT"), deposit_nft],
        [Txn.application_args[0] == Bytes("bid"), bid],
        [Txn.application_args[0] == Bytes("claimNFT"), claim_nft],
        [Txn.application_args[0] == Bytes("claimBestBid"), claim_best_bid],
        [Txn.application_args[0] == Bytes("claimlostBidMoney"), claim_lost_bid_money]
    )

    return result


if __name__ == "__main__":
    with open("auction_approval", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=3)
        f.write(compiled)

    # with open("auction_clear_state", "w") as f:
    #     compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=3)
    #     f.write(compiled)