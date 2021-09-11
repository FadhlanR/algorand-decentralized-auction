from pyteal import *


def contract():

    is_optin_escrow = Txn.sender() == Txn.asset_receiver()
    
    is_nft_claim = Gtxn[Global.group_size() - Int(1)].application_args[0] == Bytes('claim_nft')
    nft_claim = Seq([Assert(And(
            Txn.receiver() == Gtxn[Global.group_size() - Int(1)].sender(),
            Gtxn[Global.group_size() - Int(1)].application_id() == Int(000000),
            Txn.xfer_asset() == Int(111111)
        )),
        Return(Int(1))])
    
    is_money_claim = Gtxn[Global.group_size() - Int(1)].application_args[0] == Bytes('claim_money')
    money_claim = Seq([Assert(And(
            Txn.receiver() == Gtxn[Global.group_size() - Int(1)].sender(),
            Gtxn[Global.group_size() - Int(1)].application_id() == Int(000000),
            Txn.type_enum() == TxnType.Payment
         )),
        Return(Int(1))])

    is_claim_back = Gtxn[Global.group_size() - Int(1)].application_args[0] == Bytes('claim_back')
    claim_back = Seq([Assert(And(
            Txn.receiver() == Gtxn[Global.group_size() - Int(1)].sender(),
            Gtxn[Global.group_size() - Int(1)].application_id() == Int(000000),
            Txn.type_enum() == TxnType.Payment
        )),
        Return(Int(1))])


    result = Cond(
        [is_optin_escrow, Return(Int(1))],
        [is_nft_claim, nft_claim],
        [is_money_claim, money_claim],
        [is_claim_back, claim_back],
    )
    return result


if __name__ == "__main__":
    with open('./contracts/stateless_auction.teal', 'w') as f:
        compiled = compileTeal(contract(), mode=Mode.Signature, version=3)
        f.write(compiled)