from pyteal import *

def approval_program():
    on_creation = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        App.globalPut(Bytes("startDate"), Btoi(Txn.application_args[0])),
        App.globalPut(Bytes("endDate"), Btoi(Txn.application_args[1])),
        App.globalPut(Bytes("nftId"), Btoi(Txn.application_args[2])),
        App.globalPut(Bytes("nftOwner"), Txn.sender()),
        App.globalPut(Bytes("bestOffer"), Int(0)),
        App.globalPut(Bytes("bestBidder"), Global.zero_address()),
        App.globalPut(Bytes("isOpen"), Int(0)),
        App.globalPut(Bytes("isNFTClaimed"), Int(0)),
        App.globalPut(Bytes("isMoneyClaimed"), Int(0)),
        App.globalPut(Bytes("totalOffer"), Int(0)),
        App.globalPut(Bytes("statelessAddress"), Global.zero_address()),
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
            Txn.sender() != App.globalGet(Bytes("nftOwner"))), bidder_closeout],
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
        [App.globalGet(Bytes("isOpen")) == Int(0), Return(is_owner)]
    )

    on_optin = Seq([
        App.localPut(Int(0), Bytes("totalOffer"), Int(0)),
        Return(Int(1))
    ])

    open_auction = Seq([
        Assert(Txn.application_args.length() >= Int(1)),
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
    ])

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

    result = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.OptIn, on_optin],
        [Txn.application_args[0] == Bytes("openAuction"), open_auction],
        [Txn.application_args[0] == Bytes("depositNFT"), deposit_nft],
        [Txn.application_args[0] == Bytes("bid"), bid]
    )

    return result

def clear_state_program():
    program = Seq([
        App.globalPut(
            Bytes("totalOffer"),
            App.globalGet(Bytes("totalOffer")) + App.localGet(Int(0), Bytes("totalOffer"))
        ),
        Return(Int(1))
    ])

    return program

if __name__ == "__main__":
    with open('./contracts/stateful_auction_approval.teal', 'w') as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=3)
        f.write(compiled)

    with open('./contracts/stateful_auction_clear.teal', 'w') as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=3)
        f.write(compiled)