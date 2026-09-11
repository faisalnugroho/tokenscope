// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title MisleadingToken — names lie; behavior must decide
contract MisleadingToken {
    string public name = "Misleading Token";
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);

    // named "mint" but does NOT modify supply — only logs
    function mint(address, uint256) external pure returns (bool) {
        return true;
    }

    // named "blacklistCheck" but is a pure view unrelated to any list
    function blacklistCheck(address) external pure returns (bool) {
        return false;
    }

    // named "pause" but does not gate any transfer path
    function pause() external pure returns (bool) {
        return true;
    }

    // named "rescueFunds" but only returns a constant
    function rescueFunds(address) external pure returns (uint256) {
        return 0;
    }

    function transfer(address to, uint256 value) external returns (bool) {
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
