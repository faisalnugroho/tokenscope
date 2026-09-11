// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title ForcedToken — admin can move tokens between arbitrary addresses
contract ForcedToken {
    string public name = "Forced Token";
    address public owner;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event ForcedTransfer(address indexed from, address indexed to, uint256 value);

    constructor() { owner = msg.sender; }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function forceTransfer(address from, address to, uint256 value)
        external onlyOwner
    {
        require(balanceOf[from] >= value, "insufficient balance");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
        emit ForcedTransfer(from, to, value);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
