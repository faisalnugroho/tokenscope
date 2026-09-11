// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title UUPS-style upgradeable proxy with upgrade admin
contract UpgradeableToken {
    string public name = "Upgradeable Token";
    address public owner;
    address public implementation;
    address public pendingImplementation;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Upgraded(address indexed implementation);

    constructor(address impl) {
        owner = msg.sender;
        implementation = impl;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function proposeUpgrade(address newImpl) external onlyOwner {
        pendingImplementation = newImpl;
    }

    function upgrade() external onlyOwner {
        require(pendingImplementation != address(0), "no pending");
        implementation = pendingImplementation;
        pendingImplementation = address(0);
        emit Upgraded(implementation);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
