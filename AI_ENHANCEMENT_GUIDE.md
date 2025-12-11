# FuturScam AI Enhancement Integration Guide

## Overview
The ETL pipeline now includes AI-powered job description enhancement using OpenAI's GPT-4o model. Every RFP processed through the system will automatically have its job description transformed into a structured, professional HTML format with automatic categorization.

## Setup

### 1. OpenAI API Key
Add your OpenAI API key to `params.py`:
```python
OPENAI_API_KEY = "sk-proj-..."  # Your OpenAI API key
```

**Important**: If no API key is provided, the system will continue to work normally but skip the enhancement step with a warning message.

### 2. How It Works

The enhancement process is integrated into both data sources:
- **Pro Unity Emails**: Enhanced after `apply_pro_unity_defaults()`
- **Boond Opportunities**: Enhanced after `transform_boond_to_mongo_format()`

### 3. Enhancement Process

For each RFP, the system:
1. Extracts the raw `job_desc` field
2. Sends it to GPT-4o with a specialized prompt
3. Receives back:
   - `RFP_type`: Automatic categorization
   - `enhanced_job_description_html`: Structured HTML content
4. Updates the RFP document with these new fields
5. Saves to MongoDB

## RFP Type Categories

The AI automatically categorizes each RFP into one of these types:

- **Go-To-Market / Sales B2B**: Business development, sales, partnerships
- **Data / AI / BI**: Data science, analytics, machine learning
- **Integration / API / Architecture**: Systems integration, APIs, technical architecture
- **Cybersecurity**: Security, compliance, risk management
- **Cloud / Infrastructure**: Cloud platforms, DevOps, infrastructure
- **Software Engineering**: Development, full-stack, backend, frontend
- **PMO / Project Management**: Project managers, coordinators, PMO
- **Business Analysis**: Business analysts, requirements, process optimization
- **Support & Operations**: Technical support, operations, maintenance
- **Autre**: Other/miscellaneous roles

## Enhanced Job Description Structure

The HTML output includes these sections:

1. **Contexte du Projet**: Project context and background
2. **Responsabilités**: Main responsibilities and missions
3. **Profil Recherché**: Required profile and experience
4. **Compétences Techniques**: Technical skills and technologies
5. **Soft Skills**: Soft skills and personal qualities

Example output:
```html
<section id="contexte">
  <h2>Contexte du Projet</h2>
  <p>Notre client, leader dans le secteur financier...</p>
</section>
<section id="responsabilites">
  <h2>Responsabilités</h2>
  <ul>
    <li>Développer des solutions cloud...</li>
    <li>Collaborer avec les équipes...</li>
  </ul>
</section>
<!-- ... more sections ... -->
```

## MongoDB Schema Updates

Two new fields are added to each RFP document:

```json
{
  "job_id": "12345",
  "job_desc": "Original raw text...",
  "RFP_type": "Cloud / Infrastructure",
  "enhanced_job_description_html": "<section id=\"contexte\">...</section>...",
  // ... other fields
}
```

## Error Handling

The enhancement is **fault-tolerant**:
- If OpenAI API is unavailable, the original `job_desc` is preserved
- If API key is missing, enhancement is skipped with a warning
- Errors are logged but don't stop the ETL process
- RFP is saved to MongoDB regardless of enhancement success

## Performance Notes

- Enhancement adds ~2-5 seconds per RFP (API call time)
- For large batches, expect longer total processing time
- Consider rate limits on OpenAI API (depends on your tier)
- Enhancement happens sequentially to avoid overwhelming the API

## Testing

To test the integration:

1. Set your `OPENAI_API_KEY` in `params.py`
2. Run the ETL: `python .\src\main.py`
3. Check console output for:
   ```
   [INIT] ChatGPT Job Enhancer initialized
   [CHATGPT] Enhancing job description for job_id: 12345...
   [OK] Job enhanced - RFP_type: Cloud / Infrastructure
   ```
4. Verify MongoDB documents contain `RFP_type` and `enhanced_job_description_html`

## Disabling Enhancement

To disable AI enhancement without removing code:
1. Clear or comment out `OPENAI_API_KEY` in `params.py`
2. The system will automatically skip enhancement and log:
   ```
   [SKIP] Job enhancement skipped (no OpenAI API key)
   ```

## Cost Estimation

Using GPT-4o pricing (as of Dec 2024):
- Input: ~$2.50 per 1M tokens
- Output: ~$10.00 per 1M tokens
- Average job description: ~500 input tokens, ~800 output tokens
- **Estimated cost per RFP**: ~$0.01 USD

For 100 RFPs/day: ~$1/day or ~$30/month

## Troubleshooting

**Issue**: `[ERROR] Error enhancing job description: ...`
- Check API key is valid
- Verify internet connectivity
- Check OpenAI service status

**Issue**: Enhancement takes too long
- Normal for first run with many RFPs
- Consider processing in smaller batches
- Check your OpenAI API rate limits

**Issue**: HTML output not formatted correctly
- The prompt is designed for professional HR formatting
- If results are inconsistent, check the GPT-4o model availability
- Fallback to original text is automatic on errors
