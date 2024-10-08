<center><img src="https://content.henselforcongress.com/goodies/h4c_github_org.svg" alt="Hensel for Congress"/></center>

<center>Our mission is to leverage technology to bring transparency and modernization to government.</center>
<p></p>
<div id="social" align="center">
  <a href="https://henselforcongress.com" target="_blank"><img src="https://img.shields.io/badge/Campaign%20Website-3066BD?style=for-the-badge&logoColor=white" alt="Hensel for Congress Campaign Website"/></a>
  &nbsp; &nbsp; &nbsp;
  <a href="https://secure.anedot.com/hensel-for-congress/github-support" target="_blank"><img src="https://img.shields.io/badge/Donate-3066BD?style=for-the-badge&logo=donate&logoColor=white" alt="Donate to Hensel for Congress"/></a>
  &nbsp; &nbsp; &nbsp;
  <a href="https://github.com/orgs/HenselForCongress/projects/4" target="_blank"><img src="https://img.shields.io/badge/Get%20Involved-3066BD?style=for-the-badge&logoColor=white" alt="Get Involved with Hensel for Congress"/></a>
</div>


CandidateGPT is actively under development, focusing on refining features and ensuring transparent AI interactions in political discussions. We welcome contributors to explore our backlog, work on enhancing response accuracy, and help expand our data sources. Join us in shaping the future of political communication.


### How It Works
CandidateGPT employs advanced AI technology developed by OpenAI to generate context-aware and accurate chatbot responses. By using a comprehensive dataset of official documents and public statements, the bot mirrors the candidate’s positions, offering voters an interactive tool for direct and informed engagement. This setup transforms political discourse by enabling meaningful conversations between candidates and constituents.



### Note on Current Status
CandidateGPT is currently in the active development phase, with ongoing efforts to refine its features and ensure effective and transparent AI interactions within political discussions. We invite contributors to check out our backlog as we tackle immediate goals, such as improving response accuracy and expanding data sources. Feel free to engage with us and contribute to the future of political communication.


## Getting Started

1. Clone the repository:
   ```sh
   git clone https://github.com/HenselForCongress/candidategpt.git
   cd candidategpt
   ```

2. Set up environment variables:
   ```sh
   cp .env.example .env
   ```

3. Start the services using Docker Compose:
   ```sh
   docker-compose up --build
   ```

4. Access the application at `http://localhost:5024` or at the specified host and port in your environment variables.

## How to Help

- Contribute code or improvements through pull requests on GitHub. Check our [backlog for current task assignments](https://github.com/HenselForCongress/candidategpt/projects/4).
- Report issues or suggest features in our issue tracker.


## Run Security Tests

Ensuring the security of the code is essential for maintaining trust and reliability. Run a comprehensive security test using Bandit to analyze the project's Python code for vulnerabilities, common security issues, or general coding best practices. Execute the following command to initiate the test and receive a detailed report:

```sh
poetry run bandit -r .
```


## Auxiliary Services
CandidateGPT integrates with several auxiliary services to enhance its capabilities:

### Langflow
This service powers the deployment and interaction capabilities of our AI models. Check out the [Langflow GitHub repository](https://github.com/langflow-ai/langflow) for more integration details and deployment guidelines. Use the [Docker Deploy Docs](https://github.com/langflow-ai/langflow/blob/main/docker_example/docker-compose.yml) for seamless setup.

### Cloudflare AI Gateway
Cloudflare AI Gateway provides scalable and secure API access for running our AI models efficiently. It ensures reliable performance and helps manage API requests effectively. This integration enhances CandidateGPT’s ability to handle concurrent interactions and maintain responsiveness under varying loads. For more information, visit the [Cloudflare AI Gateway page](https://www.cloudflare.com/developer-platform/products/ai-gateway/).

### Sentry
Sentry supports comprehensive error monitoring and tracking, enabling us to swiftly address any issues and optimize platform performance. By integrating Sentry, we ensure that any unexpected behaviors in the system are quickly identified and resolved, maintaining a high standard of reliability and user trust. Learn more by visiting [Sentry's official site](https://sentry.io/welcome/).

## License

All repositories under the Hensel for Congress organization are licensed under the GNU Affero General Public License version 3.0 (AGPL-3.0). You are free to use, copy, distribute, and modify the software as long as any modifications or derivative works are also licensed under AGPL-3.0. This ensures that the source code remains available to users interacting with the software over a network, promoting transparency and the freedom to modify networked software.

For more details, see the [full text of the license](https://www.gnu.org/licenses/agpl-3.0.html).


Join us in reshaping political communication for a more transparent future. Whether you can contribute code, ideas, or support Bentley’s campaign, every effort makes a difference.

<div align="center">
  <table border="1" style="border-collapse: collapse; border: 2px solid black; margin-left: auto; margin-right: auto;">
    <tr>
      <td style="padding: 10px;">
        Paid for by Hensel for Congress
      </td>
    </tr>
  </table>
</div>

