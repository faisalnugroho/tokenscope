// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title RoleToken — AccessControl-style roles: ADMIN, MINTER, PAUSER
contract RoleToken {
    string public name = "Role Token";
    mapping(bytes32 => mapping(address => bool)) public hasRole;
    mapping(bytes32 => bytes32) public getRoleAdmin;
    address public admin;

    bytes32 public constant DEFAULT_ADMIN_ROLE = 0x00;
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event RoleGranted(bytes32 indexed role, address indexed account, address indexed sender);
    event RoleRevoked(bytes32 indexed role, address indexed account, address indexed sender);

    constructor() {
        admin = msg.sender;
        hasRole[DEFAULT_ADMIN_ROLE][msg.sender] = true;
        getRoleAdmin[MINTER_ROLE] = DEFAULT_ADMIN_ROLE;
        getRoleAdmin[PAUSER_ROLE] = DEFAULT_ADMIN_ROLE;
    }

    modifier onlyRole(bytes32 role) {
        require(hasRole[role][msg.sender], "missing role");
        _;
    }

    function grantRole(bytes32 role, address account)
        external onlyRole(getRoleAdmin[role])
    {
        hasRole[role][account] = true;
        emit RoleGranted(role, account, msg.sender);
    }

    function revokeRole(bytes32 role, address account)
        external onlyRole(getRoleAdmin[role])
    {
        hasRole[role][account] = false;
        emit RoleRevoked(role, account, msg.sender);
    }

    function mint(address to, uint256 value) external onlyRole(MINTER_ROLE) {
        totalSupply += value;
        balanceOf[to] += value;
        emit Transfer(address(0), to, value);
    }
}
