// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title AmbiguousToken — mixed signals: owner exists but no visible
/// privileged transfer/supply paths; storage hints at future admin use
contract AmbiguousToken {
    string public name = "Ambiguous Token";
    address public owner;
    mapping(address => uint256) public balanceOf;
    mapping(address => bool) internal _flags;

    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor() { owner = msg.sender; }

    function setFlag(address a, bool v) external {
        // NOTE: no access control modifier — anyone can set flags
        _flags[a] = v;
    }

    function transfer(address to, uint256 value) external returns (bool) {
        // flags are read but never enforced — unclear semantics
        if (_flags[msg.sender]) {
            // flagged path: behaviour identical to normal path
        }
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
