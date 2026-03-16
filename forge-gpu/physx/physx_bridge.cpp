/**
 * @file physx_bridge.cpp
 * @brief NVIDIA PhysX 5.6 bridge for FORGE.
 *
 * Language tier: GPU / C++
 * Role per Polyglot Architecture Doctrine: physics simulation at scale.
 * PhysX runs natively in C++/CUDA — no Python wrapper on the hot path.
 *
 * This file is compiled when PHYSX_ROOT is set in the CMake configuration:
 *   cmake -DPHYSX_ROOT=/opt/PhysX-106 ..
 *
 * Latency target: < 10 ms per simulation step (GPU-bound, ArticulationCache
 * data transfer is the dominant cost above ~5000 DOFs).
 *
 * Dependencies
 * ------------
 *   PhysX SDK 5.6 (https://github.com/NVIDIA-Omniverse/PhysX)
 *   CUDA 11.8+
 *   CMake option: -DFORGE_ENABLE_PHYSX=ON
 *
 * Usage (from Python via pybind11 — see physx_python_bindings.cpp)
 * ----------------------------------------------------------------
 *   import forge_physx
 *   sim = forge_physx.PhysXBridge(use_gpu=True)
 *   sim.add_rigid_body(mass=1.0, pos=[0,1,0])
 *   state = sim.step(dt=1/60)
 */

// PhysX headers — only compiled when FORGE_ENABLE_PHYSX is ON
#ifdef FORGE_ENABLE_PHYSX

#include <PxPhysicsAPI.h>
#include <extensions/PxDefaultAllocator.h>
#include <extensions/PxDefaultErrorCallback.h>
#include <extensions/PxDefaultSimulationFilterShader.h>

#include <cstdio>
#include <stdexcept>
#include <vector>

namespace forge::gpu::physx_bridge {

namespace {

class ForgeErrorCallback : public physx::PxErrorCallback {
public:
    void reportError(physx::PxErrorCode::Enum code,
                     const char* message,
                     const char* file, int line) override
    {
        std::fprintf(stderr, "[PhysX] %s (%s:%d) code=%d\n",
                     message, file, line, static_cast<int>(code));
    }
};

static physx::PxDefaultAllocator  g_allocator;
static ForgeErrorCallback          g_error_cb;

} // anonymous namespace

class PhysXBridge {
public:
    explicit PhysXBridge(bool use_gpu = true) {
        foundation_ = PxCreateFoundation(
            PX_PHYSICS_VERSION, g_allocator, g_error_cb);
        if (!foundation_) throw std::runtime_error("PxCreateFoundation failed");

        physics_ = PxCreatePhysics(
            PX_PHYSICS_VERSION, *foundation_,
            physx::PxTolerancesScale{}, true, nullptr);
        if (!physics_) throw std::runtime_error("PxCreatePhysics failed");

        physx::PxSceneDesc scene_desc(physics_->getTolerancesScale());
        scene_desc.gravity = physx::PxVec3(0.0f, -9.81f, 0.0f);
        scene_desc.filterShader = physx::PxDefaultSimulationFilterShader;

        if (use_gpu) {
            physx::PxCudaContextManagerDesc cm_desc;
            cuda_ctx_ = PxCreateCudaContextManager(
                *foundation_, cm_desc, PxGetProfilerCallback());
            if (cuda_ctx_ && cuda_ctx_->contextIsValid()) {
                scene_desc.cudaContextManager = cuda_ctx_;
                scene_desc.flags |=
                    physx::PxSceneFlag::eENABLE_GPU_DYNAMICS;
                scene_desc.broadPhaseType =
                    physx::PxBroadPhaseType::eGPU;
            }
        }

        auto* dispatcher = physx::PxDefaultCpuDispatcherCreate(2);
        scene_desc.cpuDispatcher = dispatcher;

        scene_ = physics_->createScene(scene_desc);
        if (!scene_) throw std::runtime_error("createScene failed");
    }

    ~PhysXBridge() {
        if (scene_)    scene_->release();
        if (physics_)  physics_->release();
        if (cuda_ctx_) cuda_ctx_->release();
        if (foundation_) foundation_->release();
    }

    PhysXBridge(const PhysXBridge&) = delete;
    PhysXBridge& operator=(const PhysXBridge&) = delete;

    /// Advance the simulation by dt seconds.
    void step(float dt) {
        scene_->simulate(dt);
        scene_->fetchResults(/*block=*/true);
    }

private:
    physx::PxFoundation*           foundation_{nullptr};
    physx::PxPhysics*              physics_{nullptr};
    physx::PxCudaContextManager*   cuda_ctx_{nullptr};
    physx::PxScene*                scene_{nullptr};
};

} // namespace forge::gpu::physx_bridge

#endif // FORGE_ENABLE_PHYSX
