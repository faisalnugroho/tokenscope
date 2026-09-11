// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title PausableToken — owner can pause all transfers
contract PausableToken {
    string public name = "Pausable Token";
    address public owner;
    bool public paused;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Paused(address account);
    event Unpaused(address account);

    constructor() { owner = msg.sender; }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function pause() external onlyOwner { paused = true; emit Paused(msg.sender); }
    function unpause() external onlyOwner { paused = false; emit Unpaused(msg.sender); }

    function transfer(address to, uint256 value) external returns (bool) {
        require(!paused, "transfers paused");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
