// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title FeeToken — owner changes the transfer fee rate + recipient
contract FeeToken {
    string public name = "Fee Token";
    address public owner;
    uint256 public feeBps = 25; // 0.25%
    address public feeRecipient;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event FeeUpdated(uint256 newFeeBps);
    event FeeRecipientUpdated(address newRecipient);

    constructor() { owner = msg.sender; feeRecipient = msg.sender; }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function setFee(uint256 bps) external onlyOwner {
        require(bps <= 1000, "fee too high");
        feeBps = bps;
        emit FeeUpdated(bps);
    }

    function setFeeRecipient(address r) external onlyOwner {
        feeRecipient = r;
        emit FeeRecipientUpdated(r);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        uint256 fee = (value * feeBps) / 10000;
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value - fee;
        balanceOf[feeRecipient] += fee;
        emit Transfer(msg.sender, to, value - fee);
        emit Transfer(msg.sender, feeRecipient, fee);
        return true;
    }
}
