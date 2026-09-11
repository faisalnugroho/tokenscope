// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title BlacklistToken — owner-maintained blocklist in the transfer path
contract BlacklistToken {
    string public name = "Blacklist Token";
    address public owner;
    mapping(address => bool) public blacklisted;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Blacklisted(address indexed account);
    event Unblacklisted(address indexed account);

    constructor() { owner = msg.sender; }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function blacklist(address account) external onlyOwner {
        blacklisted[account] = true;
        emit Blacklisted(account);
    }

    function unblacklist(address account) external onlyOwner {
        blacklisted[account] = false;
        emit Unblacklisted(account);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(!blacklisted[msg.sender], "sender blacklisted");
        require(!blacklisted[to], "recipient blacklisted");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
