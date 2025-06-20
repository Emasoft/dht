#!/bin/bash
# Demo script to showcase workspace functionality

echo "========================================="
echo "DHT Workspace Demo"
echo "========================================="
echo

echo "1. Setting up the workspace..."
echo "   Running: dhtl setup"
echo

echo "2. Listing all available scripts in workspace:"
echo "   Running: dhtl ws run --list"
echo

echo "3. Running script in all members:"
echo "   Running: dhtl ws run test"
echo

echo "4. Running script in specific member:"
echo "   Running: dhtl workspace core run core-hello"
echo

echo "5. Executing shell command in all members:"
echo '   Running: dhtl ws exec -- echo "Working in: $PWD"'
echo

echo "6. Running root project only:"
echo "   Running: dhtl project run demo-root"
echo

echo "7. Using filters:"
echo '   Running: dhtl ws run test --only "packages/*"'
echo

echo "========================================="
echo "To run these commands yourself:"
echo "cd examples/workspace-demo"
echo "dhtl setup"
echo "Then try the commands above!"
echo "========================================="
