// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title BurnableToken — holders burn their own tokens
contract BurnableToken {
    string public name = "Burnable Token";
    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Burned(address indexed from, uint256 value);

    function burn(uint256 value) external {
        require(balanceOf[msg.sender] >= value, "insufficient balance");
        balanceOf[msg.sender] -= value;
        totalSupply -= value;
        emit Transfer(msg.sender, address(0), value);
        emit Burned(msg.sender, value);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
