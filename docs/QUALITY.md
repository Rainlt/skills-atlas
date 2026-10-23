# 质量与待核实记录

这是结构检查与上游声明记录，不是人工评测、安全扫描或许可结论。

| 指标 | 条目数 |
|---|---:|
| 缺少技能级许可声明，需核实具体授权 | 2778 |
| 名称、目录或 frontmatter 等格式问题 | 98 |
| 含父目录引用或插件根目录变量等依赖线索 | 175 |
| 有上游自报 risk 字段 | 2690 |

各指标可以重叠。未标注风险不表示安全；有 license 字段也不表示宽松开源。完整字段可用 `atlas.py show <ID>` 查看。

格式问题示例（最多 100 项；完整列表在 catalog 的 format_issues）：

| 条目 | 记录 |
|---|---|
| `ComposioHQ/awesome-claude-skills/composio-skills/-21risk-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/-2chat-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/ahrefs-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/anthropic_administrator-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/apify-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/apollo-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/ashby-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/attio-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/braintree-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/capsule-crm-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/capsule_crm-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/clockify-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/cloudinary-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/coinbase-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/contentful-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/customerio-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/docker-hub-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/docker_hub-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/dynamics365-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/elevenlabs-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/eventbrite-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/excel-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/facebook-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/fillout_forms-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/firecrawl-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/freshbooks-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/gong-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/google_admin-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/google_classroom-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/google_maps-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/google_search_console-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/gorgias-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/groqcloud-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/gumroad-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/harvest-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/heygen-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/hunter-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/instantly-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/jotform-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/kommo-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/launch-darkly-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/launch_darkly-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/lemlist-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/lemon-squeezy-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/lemon_squeezy-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/lever-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/mailerlite-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/many_chat-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/microsoft-clarity-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/microsoft_clarity-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/mistral-ai-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/mistral_ai-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/neon-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/netsuite-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/new-relic-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/new_relic-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/omnisend-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/onesignal_rest_api-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/openai-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/pandadoc-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/phantombuster-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/prismic-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/productboard-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/quickbooks-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/ramp-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/replicate-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/ring-central-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/ring_central-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/semrush-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/share-point-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/share_point-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/shortcut-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/similarweb_digitalrank_api-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/snowflake-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/spotify-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/survey-monkey-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/survey_monkey-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/toggl-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/uploadcare-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/wave-accounting-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/wave_accounting-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/webex-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/workday-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/xero-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/zoho-books-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/zoho-desk-automation` | name_directory_mismatch, nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/zoho_bigin-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/zoho_books-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/zoho_desk-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/zoho_inventory-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/zoho_invoice-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/composio-skills/zoho_mail-automation` | nonstandard_name |
| `ComposioHQ/awesome-claude-skills/video-downloader` | name_directory_mismatch |
| `sickn33/agentic-awesome-skills/skills/android_ui_verification` | nonstandard_name |
| `vercel-labs/agent-skills/skills/composition-patterns` | name_directory_mismatch |
| `vercel-labs/agent-skills/skills/react-best-practices` | name_directory_mismatch |
| `vercel-labs/agent-skills/skills/react-native-skills` | name_directory_mismatch |
| `vercel-labs/agent-skills/skills/react-view-transitions` | name_directory_mismatch |
