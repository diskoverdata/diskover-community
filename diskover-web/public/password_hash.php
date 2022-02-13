<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2021 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

require '../vendor/autoload.php';
use diskover\Constants;
error_reporting(E_ERROR | E_PARSE);

// password form submitted
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['password'])) {
   $password = $_POST['password'];
   // encrypt password
   $password_hash = password_hash($password, PASSWORD_DEFAULT);
}

?>

<!DOCTYPE html>
<html lang="en">

<head>
   <?php if (isset($_COOKIE['sendanondata']) && $_COOKIE['sendanondata'] == 1) { ?>
   <!-- Global site tag (gtag.js) - Google Analytics -->
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-DYSE689C04"></script>
   <script>
   window.dataLayer = window.dataLayer || [];
   function gtag(){dataLayer.push(arguments);}
   gtag('js', new Date());

   gtag('config', 'G-DYSE689C04');
   </script>
   <?php } ?>
   <meta charset="utf-8">
   <meta http-equiv="X-UA-Compatible" content="IE=edge" />
   <meta name="viewport" content="width=device-width, initial-scale=1">
   <title>diskover &mdash; Password Hash Generator</title>
   <link rel="stylesheet" href="css/fontawesome-free/css/all.min.css" media="screen" />
   <link rel="stylesheet" href="css/bootswatch.min.css" media="screen" />
   <link rel="stylesheet" href="css/diskover.css" media="screen" />
   <link rel="icon" type="image/png" href="images/diskoverfavico.png" />
   <style>
      .passwordhashgen-logo {
         text-align: center;
         padding: 40px 0 0 0;
      }

      .passwordhashgen {
         width: 550px;
         background-color: #1C1E21;
         box-shadow: 0 0 9px 0 rgba(0, 0, 0, 0.3);
         margin: 100px auto;
         padding: 0 20px 20px 20px;
      }

      .passwordhashgen h1 {
         text-align: center;
         color: #ffffff;
         font-size: 24px;
         padding: 0 0 5px 0;
      }

      .passwordhashgen p {
         text-align: center;
         color: lightgray;
         font-size: 14px;
      }
   </style>
</head>

<body>
   <div class="passwordhashgen">
      <div class="passwordhashgen-logo"><img src="images/diskover.png" alt="diskover" width="249" height="189" /></div>
         <h1>Password Hash Generator</h1>
         <p>Enter a strong password and click hash password to create a hash of your password. Set this hashed password in your diskover-web config file.</p>
         <form class="form-horizontal" action="<?php echo htmlspecialchars($_SERVER['PHP_SELF']); ?>" method="post">
            <div class="form-group">
               <label for="password" class="col-lg-2 control-label"><i class="fas fa-lock"></i> </label>
               <div class="col-lg-10">
                  <input type="password" class="form-control password-input" id="password" name="password" placeholder="Password" autocomplete="off" required>
               </div>
            </div>   
            <div class="form-group">
               <div class="col-lg-10 col-lg-offset-2">
                  <button type="submit" class="btn btn-primary">Hash Password</button>
               </div>
            </div>
         </form>
      <?php if (isset($password_hash)) { ?>
      <p>Password: </p>
      <p><?php echo $password; ?></p>
      <p>Password Hash: </p>
      <p id="passwordHash"><?php echo $password_hash; ?></p>
      <button onclick="copyToClipboard('#passwordHash')" class="btn btn-primary">Copy Hash</button>
      <?php } ?>
   </div>
</body>
<script language="javascript" src="js/jquery.min.js"></script>
<script type="text/javascript">
   function copyToClipboard(element) {
      var $temp = $("<input>");
      $("body").append($temp);
      $temp.val($(element).text()).select();
      document.execCommand("copy");
      $temp.remove();
      alert("Copied hash");
   }
</script>
</html>