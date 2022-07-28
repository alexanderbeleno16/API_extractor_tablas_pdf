<?php
ob_start();
        
system("python3 " . __DIR__ ."/../Py/file.py parametro_prueba");

$result = ob_get_contents();

ob_end_clean();