#!/bin/bash

# incase runServer.sh didn't close ports properly
kill $( lsof -i:44444 -t );
kill $( lsof -i:50001 -t );
kill $( lsof -i:50002 -t );
kill $( lsof -i:50003 -t );
