// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title MintableToken — owner can mint
import "./IP.sol";
contract MintableToken is Ownable {
    string public name = "Mintable Token";
    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Minted(address indexed to, uint256 value);

    constructor() { _transferOwnership(msg.sender); }

    function mint(address to, uint256 value) external onlyOwner {
        totalSupply += value;
        balanceOf[to] += value;
        emit Transfer(address(0), to, value);
        emit Minted(to, value);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
