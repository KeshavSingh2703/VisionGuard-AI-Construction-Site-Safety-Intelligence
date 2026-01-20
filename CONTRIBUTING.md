# Contributing to SecureOps

Thank you for your interest in contributing to SecureOps! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## 🔧 Development Process

1.  **Fork the repo** and create your branch from `main`.
2.  **Clone the repository** to your local machine.
3.  **Install dependencies** for both backend and frontend (see README).
4.  **Create a branch** for your feature or fix:
    ```bash
    git checkout -b feature/amazing-feature
    # or
    git checkout -b fix/annoying-bug
    ```

## 👩‍💻 Coding Standards

### Backend (Python)
- Follow **PEP 8**.
- Use **Type Hints** for all function arguments and return values.
- Ensure all new modules have corresponding unit tests in `tests/`.
- Run formatting compliance implies strict adherence to the project style (no messy imports).

### Frontend (React)
- Use **Functional Components** and Hooks.
- Avoid inline styles; use **TailwindCSS** utility classes.
- Ensure authentication logic goes through the `AuthContext` and `api.js` interceptors.

## 🧪 Testing

Before submitting a Pull Request, please ensure tests pass:

```bash
# Backend
cd secureops-backend
pytest

# Frontend
cd secureops-frontend
npm run lint
```

## 📬 Pull Request Process

1.  Update the `README.md` with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
2.  Increase the version numbers in any examples files and the README to the new version that this Pull Request would represent.
3.  You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## 📝 License

By contributing, you agree that your contributions will be licensed under its MIT License.
