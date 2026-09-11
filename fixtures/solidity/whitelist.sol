// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title WhitelistToken — allowlist gates all transfers
contract WhitelistToken {
    string public name = "Whitelist Token";
    address public owner;
    mapping(address => bool) public allowed;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Allowed(address indexed account);
    event Removed(address indexed account);

    constructor() { owner = msg.sender; }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function allow(address account) external onlyOwner {
        allowed[account] = true;
        emit Allowed(account);
    }

    function remove(address account) external onlyOwner {
        allowed[account] = false;
        emit Removed(account);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(allowed[msg.sender], "sender not allowed");
        require(allowed[to], "recipient not allowed");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
