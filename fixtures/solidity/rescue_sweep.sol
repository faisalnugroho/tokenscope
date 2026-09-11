// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

/// @title RescueToken — owner sweeps arbitrary ERC20s + withdraws ETH
interface IERC20 {
    function transfer(address to, uint256 value) external returns (bool);
    function balanceOf(address a) external view returns (uint256);
}

contract RescueToken {
    string public name = "Rescue Token";
    address public owner;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Rescued(address indexed token, address indexed to, uint256 value);
    event EthWithdrawn(address indexed to, uint256 value);

    constructor() { owner = msg.sender; }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function rescueTokens(IERC20 token, address to) external onlyOwner {
        uint256 amount = token.balanceOf(address(this));
        require(token.transfer(to, amount), "rescue failed");
        emit Rescued(address(token), to, amount);
    }

    function withdrawEth(address to) external onlyOwner {
        uint256 amount = address(this).balance;
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "eth transfer failed");
        emit EthWithdrawn(to, amount);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    receive() external payable {}
}
