# koto-blockchain-parser
A blockchain parser for the Koto cryptocyrrency, which originated from Japan on December 2017 and based on Zcash.

If you like this script, please tip me at
  Monacoin: M9VkYEVo59mQUsWt9tRDfNi6b9SBNqMSyz
  BitZeny:  ZgD57J2vDBTBcSXgg814Fr8MrgNqpyC3n6

# How to set up and get it to work
1. Setup your kotod somewhere. it'll do well on VPS or your local environment or whatever.
2. Modify config_sample.py to suit to your situation and rename it to config.py
3. python3 process_block_test.py
4. If all test cases passed, it works.

Currently the script just allows you to decode raw block string from a block hash, though I will extend the script to parse all blockchains from LevelDB anyway.

# 使い方
Kotodをビルドしてどこかでサーバー化させた後、 config_example.pyを編集してconfig.pyにリネームし、python3 procss_block_test.pyが成功すれば動いています
